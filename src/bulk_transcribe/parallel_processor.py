"""
Parallel Transcript Processor

Enables concurrent transcript extraction using ThreadPoolExecutor.
Designed to work with Streamlit's threading constraints:
- Worker threads do extraction work
- Main thread handles all UI updates
- Results are collected via queue for main thread consumption

Uses threading (not multiprocessing or async) because:
- Our bottleneck is I/O (network requests take 1-5 seconds)
- Threading allows CPU to switch tasks while waiting on network
- Simpler than async (no code rewrite needed)
- Less overhead than multiprocessing
"""

import logging
import os
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.bulk_transcribe.youtube_transcript import TranscriptResult

logger = logging.getLogger(__name__)


@dataclass
class VideoTask:
    """A single video processing task."""
    row_index: int
    youtube_url: str
    video_id: str
    title: str
    row_data: Dict[str, Any]
    # Added after processing
    result: Optional[TranscriptResult] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    status: str = "pending"  # pending, processing, completed, failed


@dataclass
class ProcessingResult:
    """Result of processing a single video task."""
    task: VideoTask
    success: bool
    transcript_result: Optional[TranscriptResult] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class BatchProgress:
    """Progress tracking for a batch of videos."""
    total: int = 0
    completed: int = 0
    successful: int = 0
    failed: int = 0
    in_progress: int = 0
    results: List[ProcessingResult] = field(default_factory=list)


class ParallelTranscriptProcessor:
    """
    Parallel processor for transcript extraction.
    
    Uses ThreadPoolExecutor to process multiple videos concurrently.
    Results are collected via a thread-safe queue that the main thread
    can poll for UI updates.
    
    Example usage:
        processor = ParallelTranscriptProcessor(max_workers=5)
        
        # Submit all tasks
        for task in tasks:
            processor.submit(task)
        
        # Poll for results (in main thread, for UI updates)
        while not processor.is_complete():
            result = processor.get_next_result(timeout=0.1)
            if result:
                update_ui(result)
        
        # Get final summary
        progress = processor.get_progress()
    """
    
    def __init__(
        self,
        max_workers: int = 2,
        extraction_func: Optional[Callable[[str], TranscriptResult]] = None,
    ):
        """
        Initialize the parallel processor.
        
        Args:
            max_workers: Number of concurrent workers (default: 2 for micro-testing)
            extraction_func: Function to extract transcript from URL.
                           If None, uses get_proxy_transcript.
        """
        self.max_workers = max_workers
        self._extraction_func = extraction_func
        
        # Thread pool and synchronization
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: Dict[Future, VideoTask] = {}
        self._results_queue: queue.Queue[ProcessingResult] = queue.Queue()
        self._lock = threading.Lock()
        
        # Progress tracking
        self._progress = BatchProgress()
        self._is_started = False
        self._should_stop = False
        
        logger.info(f"ParallelTranscriptProcessor initialized with {max_workers} workers")
    
    def _get_extraction_func(self) -> Callable[[str], TranscriptResult]:
        """Get the extraction function, lazy-loading default if needed."""
        if self._extraction_func is None:
            from src.bulk_transcribe.proxy_transcript import get_proxy_transcript
            self._extraction_func = get_proxy_transcript
        return self._extraction_func
    
    def start(self) -> None:
        """Start the thread pool executor."""
        if self._executor is not None:
            return
        
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="transcript_worker"
        )
        self._is_started = True
        self._should_stop = False
        logger.info(f"Started thread pool with {self.max_workers} workers")
    
    def stop(self, wait: bool = True) -> None:
        """
        Stop the processor and optionally wait for pending tasks.
        
        Args:
            wait: If True, wait for pending tasks to complete
        """
        self._should_stop = True
        
        if self._executor is not None:
            self._executor.shutdown(wait=wait, cancel_futures=not wait)
            self._executor = None
            self._is_started = False
            logger.info("Thread pool stopped")
    
    def submit(self, task: VideoTask) -> bool:
        """
        Submit a video task for processing.
        
        Args:
            task: VideoTask to process
            
        Returns:
            True if submitted successfully, False otherwise
        """
        if self._executor is None:
            self.start()
        
        if self._should_stop:
            logger.warning("Cannot submit task - processor is stopping")
            return False
        
        with self._lock:
            self._progress.total += 1
            self._progress.in_progress += 1
            task.status = "processing"
        
        future = self._executor.submit(self._process_task, task)
        self._futures[future] = task
        future.add_done_callback(self._on_task_complete)
        
        logger.debug(f"Submitted task for video: {task.video_id}")
        return True
    
    def submit_batch(self, tasks: List[VideoTask]) -> int:
        """
        Submit multiple tasks at once.
        
        Args:
            tasks: List of VideoTasks to process
            
        Returns:
            Number of tasks successfully submitted
        """
        submitted = 0
        for task in tasks:
            if self.submit(task):
                submitted += 1
        return submitted
    
    def _process_task(self, task: VideoTask) -> ProcessingResult:
        """
        Process a single video task (runs in worker thread).
        
        This method should NOT call any Streamlit commands.
        """
        start_time = time.time()
        
        try:
            if self._should_stop:
                return ProcessingResult(
                    task=task,
                    success=False,
                    error_message="Processing stopped by user",
                    processing_time=0.0,
                )
            
            extraction_func = self._get_extraction_func()
            transcript_result = extraction_func(task.youtube_url)
            
            processing_time = time.time() - start_time
            
            if transcript_result.success:
                logger.info(
                    f"Successfully extracted transcript for {task.video_id} "
                    f"in {processing_time:.2f}s"
                )
                return ProcessingResult(
                    task=task,
                    success=True,
                    transcript_result=transcript_result,
                    processing_time=processing_time,
                )
            else:
                logger.warning(
                    f"Failed to extract transcript for {task.video_id}: "
                    f"{transcript_result.error_message}"
                )
                return ProcessingResult(
                    task=task,
                    success=False,
                    transcript_result=transcript_result,
                    error_message=transcript_result.error_message,
                    processing_time=processing_time,
                )
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Exception during extraction: {str(e)}"
            logger.error(f"Error processing {task.video_id}: {error_msg}")
            
            return ProcessingResult(
                task=task,
                success=False,
                error_message=error_msg,
                processing_time=processing_time,
            )
    
    def _on_task_complete(self, future: Future) -> None:
        """Callback when a task completes (runs in worker thread)."""
        task = self._futures.pop(future, None)
        
        try:
            result = future.result()
        except Exception as e:
            # This shouldn't happen since we catch exceptions in _process_task
            result = ProcessingResult(
                task=task,
                success=False,
                error_message=f"Future exception: {str(e)}",
                processing_time=0.0,
            )
        
        # Update task status
        if task:
            task.status = "completed" if result.success else "failed"
            task.result = result.transcript_result
            task.processing_time = result.processing_time
            if not result.success:
                task.error = result.error_message
        
        # Update progress counters (thread-safe)
        with self._lock:
            self._progress.completed += 1
            self._progress.in_progress -= 1
            if result.success:
                self._progress.successful += 1
            else:
                self._progress.failed += 1
            self._progress.results.append(result)
        
        # Put result in queue for main thread to consume
        self._results_queue.put(result)
    
    def get_next_result(self, timeout: float = 0.1) -> Optional[ProcessingResult]:
        """
        Get the next completed result (call from main thread).
        
        This is non-blocking if timeout is small. Use this to poll
        for results while keeping the main thread responsive.
        
        Args:
            timeout: Maximum seconds to wait for a result
            
        Returns:
            ProcessingResult if available, None otherwise
        """
        try:
            return self._results_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_pending_results(self) -> List[ProcessingResult]:
        """
        Get all currently available results (non-blocking).
        
        Returns:
            List of all results currently in the queue
        """
        results = []
        while True:
            try:
                result = self._results_queue.get_nowait()
                results.append(result)
            except queue.Empty:
                break
        return results
    
    def get_progress(self) -> BatchProgress:
        """Get current progress (thread-safe snapshot)."""
        with self._lock:
            return BatchProgress(
                total=self._progress.total,
                completed=self._progress.completed,
                successful=self._progress.successful,
                failed=self._progress.failed,
                in_progress=self._progress.in_progress,
                results=list(self._progress.results),
            )
    
    def is_complete(self) -> bool:
        """Check if all submitted tasks are complete."""
        with self._lock:
            return (
                self._progress.total > 0 and
                self._progress.completed >= self._progress.total and
                self._progress.in_progress == 0
            )
    
    def pending_count(self) -> int:
        """Get the number of pending/in-progress tasks."""
        with self._lock:
            return self._progress.in_progress
    
    def request_stop(self) -> None:
        """Request graceful stop (finish current tasks, don't start new ones)."""
        self._should_stop = True
        logger.info("Stop requested - will finish current tasks")


def create_video_task(
    row_index: int,
    youtube_url: str,
    video_id: str,
    title: str,
    row_data: Optional[Dict[str, Any]] = None,
) -> VideoTask:
    """
    Helper function to create a VideoTask.
    
    Args:
        row_index: Index of the row in the input data
        youtube_url: YouTube video URL
        video_id: Extracted video ID
        title: Video title
        row_data: Optional dict with additional row data
        
    Returns:
        VideoTask ready for submission
    """
    return VideoTask(
        row_index=row_index,
        youtube_url=youtube_url,
        video_id=video_id,
        title=title,
        row_data=row_data or {},
    )
