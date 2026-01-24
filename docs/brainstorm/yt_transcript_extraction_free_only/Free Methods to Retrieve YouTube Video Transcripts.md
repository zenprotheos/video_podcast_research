# Free Methods to Retrieve YouTube Video Transcripts

Retrieving transcripts (subtitles) from YouTube videos can be achieved through various unofficial, **free** methods. These approaches do **not** require YouTube’s official Data API (which doesn’t provide transcripts and has strict quotas[[1]](https://scrapecreators.com/blog/unofficial-youtube-api#:~:text=YouTube%20can%20supercharge%20your%20content,with%20a%20sleek%20REST%20interface)[[2]](https://scrapecreators.com/blog/unofficial-youtube-api#:~:text=While%20the%20official%20YouTube%20API,JSON%2C%20ready%20for%20your%20workflows)). Instead, they rely on scraping the same caption data used in YouTube’s web interface. Below, we outline multiple Python-based solutions, along with their usage and considerations. Each method can fetch **manually provided captions** and **auto-generated captions** (if available) without an API key. We also discuss how to avoid rate limits and IP blocks when using these methods.

## Method 1: Using the youtube-transcript-api Library

The [**youtube-transcript-api**](https://pypi.org/project/youtube-transcript-api/) (Python) is a high-level, easy-to-use library specifically for YouTube transcripts[[3]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=Python%27s%20%60youtube,of%20all%2C%20it%27s%20actively%20maintained). It requires no API key or browser automation, yet supports multiple languages and even on-the-fly translation. Key features of this library include:

·       **Easy transcript retrieval:** With a single call you can get a list of caption entries (text with timestamps). For example:

from youtube_transcript_api import YouTubeTranscriptApi  
video_id = "dQw4w9WgXcQ"  # YouTube video ID or URL  
transcript = YouTubeTranscriptApi.get_transcript(video_id)  
for entry in transcript:  
    print(f"[{entry['start']:.2f}s] {entry['text']}")

This returns a list of dictionaries with keys 'text', 'start' (start time in seconds), and 'duration'[[4]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=video_id%20%3D%20%22dQw4w9WgXcQ%22%20%20,get_transcript%28video_id). Each dictionary represents one subtitle snippet.

·       **Automatic vs. manual captions:** The library will default to a manually-created transcript if available, otherwise it falls back to the auto-generated one, for the default language (English by default)[[5]](https://github.com/jdepoix/youtube-transcript-api#:~:text=By%20default%20this%20module%20always,in%20the%20requested%20language%20is). You can also **specify languages** in order of preference. For example, YouTubeTranscriptApi.get_transcript(video_id, languages=['es','en']) will try Spanish, then English[[6]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=video_id%20%3D%20). It’s wise to first check what languages exist using list_transcripts:

transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)  
for transcript in transcript_list:  
    print(f"Language: {transcript.language_code}, generated: {transcript.is_generated}")

This will list available caption tracks, indicating each track’s language code and whether it’s auto-generated[[7]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=for%20transcript%20in%20transcript_list%3A%20print%28f,print). The library provides methods to filter for only manually-created or only auto-generated tracks if needed[[5]](https://github.com/jdepoix/youtube-transcript-api#:~:text=By%20default%20this%20module%20always,in%20the%20requested%20language%20is).

- **Translated captions:** A unique feature is built-in translation. If a transcript is available (manual or auto) in one language, you can request a translated version via YouTube’s caption translation feature. For example, after retrieving a transcript object, transcript.translate('de').fetch() would give a German translation[[8]](https://github.com/jdepoix/youtube-transcript-api#:~:text=transcript%20%3D%20transcript_list.find_transcript%28,fetch). This uses YouTube’s own translation service behind the scenes.
- **Output formatting:** By default you get a Python list of subtitle entries, but the library also offers formatter classes to output JSON, plain text, WebVTT (.vtt), SRT (.srt), etc.[[9]](https://github.com/jdepoix/youtube-transcript-api#:~:text=Formatters%20are%20meant%20to%20be,separated%20format%20%28%60.csv%60%29%2C%20etc)[[10]](https://github.com/jdepoix/youtube-transcript-api#:~:text=,SRTFormatter). For instance, you can do:

from youtube_transcript_api.formatters import TextFormatter  
raw_data = YouTubeTranscriptApi.get_transcript(video_id)  
text = TextFormatter().format_transcript(raw_data)  
print(text)  # full transcript as plain text

This can be useful if you need the whole transcript as one string or in a specific subtitle file format.

**Why use youtube-transcript-api?** It is actively maintained to adapt to YouTube’s changes and is regarded as one of the most reliable ways to get transcripts in 2026[[3]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=Python%27s%20%60youtube,of%20all%2C%20it%27s%20actively%20maintained). It handles the parsing of YouTube’s internal API or HTML for you. In many cases, this library is the quickest solution.

**Potential drawbacks:** If you deploy code on cloud servers (AWS, GCP, etc.) or make _very_ large numbers of requests, YouTube may start blocking those IPs, leading the library to raise exceptions like RequestBlocked[[11]](https://github.com/jdepoix/youtube-transcript-api#:~:text=Unfortunately%2C%20YouTube%20has%20started%20blocking,is%20the%20most%20reliable%20option). The library creator notes that known cloud IP ranges are often preemptively blocked by YouTube[[11]](https://github.com/jdepoix/youtube-transcript-api#:~:text=Unfortunately%2C%20YouTube%20has%20started%20blocking,is%20the%20most%20reliable%20option). In a normal personal-use environment with modest request rates, this may not occur, but it’s something to be aware of (we cover workarounds in the **Rate Limiting** section below).

## Method 2: Using PyTube to Access Captions

[Pytube](https://pytube.io/) is a general-purpose YouTube video downloader library, but it also allows accessing caption tracks. This can be handy if you’re already using Pytube for other tasks or want a single library to get both videos and transcripts. Using Pytube for captions works as follows:

·       **Getting caption tracks:** Instantiate a YouTube object with the video URL or ID, and use the .captions attribute. For example:

from pytube import YouTube  
yt = YouTube("https://www.youtube.com/watch?v=XJGiS83eQLk")  
captions = yt.captions   
print(captions.all())

The captions.all() will return a list of Caption objects[[12]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=Subtitle%2FCaption%20Tracks%C2%B6). Each Caption has a language name and code. Notably, _auto-generated captions do appear in this list_ – they are typically labeled with the language name plus " (auto-generated)" in the lang field[[13]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=,el). For example, you might see entries like _<Caption lang="English (auto-generated)" code="en">_ alongside <Caption lang="English" code="en">[[13]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=,el) if a video has both types.

- **Selecting a caption:** You can retrieve a specific caption track by language code. For instance, caption = yt.captions.get_by_language_code('en'). Be careful if both a manual and an auto English exist – Pytube may return one of them by default. To explicitly choose the auto-generated one, you might need to iterate through captions and pick the entry where caption.name contains "auto-generated".
- **Downloading or getting the text:** Once you have a Caption object, you can get the caption text data. Pytube provides two main ways:

·       caption.xml_captions – returns the raw caption XML (YouTube’s internal timedtext XML format)[[14]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=%3E%3E%3E%20caption.xml_captions%20%27%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22utf,39).

·       caption.generate_srt_captions() – returns a string in SRT subtitle format (with indexed lines and timestamps)[[15]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=%3E%3E%3E%20print%28caption.generate_srt_captions%28%29%29%201%20000%3A000%3A00%2C000%20,dont%20know%20what%20to%20type).

For example:

caption = yt.captions['en']  # shorthand access by code  
srt_text = caption.generate_srt_captions()  
print(srt_text[:200])  # print first 200 chars of SRT text

This will output something like:

1 00:00:00,000 --> 00:00:05,541   
[Subtitle text line 1] … 

showing the typical SRT numbered captions with timestamps[[15]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=%3E%3E%3E%20print%28caption.generate_srt_captions%28%29%29%201%20000%3A000%3A00%2C000%20,dont%20know%20what%20to%20type). You can parse this or strip the timing if you only need plain text.

Using Pytube gives you the **flexibility** to retrieve captions in multiple formats. It’s especially useful if you need to programmatically download the caption file itself – e.g., you could save the SRT text to a file or parse the XML for more structured data. Pytube will handle obtaining the caption track download URL behind the scenes.

**Caveats:** Pytube’s primary focus is video streams, and it relies on YouTube’s webpage structure. It might occasionally break when YouTube changes its site, though it’s usually quickly patched by the community. Also, fetching captions via Pytube still involves making web requests to YouTube, so you face the same potential rate-limit issues as other scraping methods (Pytube doesn’t have built-in rate limit handling for captions beyond what you implement). For a handful of videos or occasional use, it should work fine. If doing bulk scraping, you’ll need to throttle requests (see **Rate Limiting** below).

## Method 3: Using yt-dlp to Download Subtitles

Another powerful option is [**yt-dlp**](https://github.com/yt-dlp/yt-dlp), a popular fork of youtube-dl. While primarily used to download video/audio, yt-dlp can also fetch subtitles/captions. It can retrieve both manual and auto-generated subtitles and save them to files in your chosen format. You can use yt-dlp either via its CLI or as a Python library:

·       **CLI usage:** You could run a command like:

    yt-dlp --skip-download --write-sub --write-auto-sub --sub-lang en --sub-format "srt" "<YouTube-URL>"

          This tells yt-dlp to skip video download and write subtitles. --write-sub gets manual subtitles (if available), --write-auto-sub gets the auto-generated (you can use both flags to get whichever exists), and --sub-lang en specifies English (adjust the code for other languages as needed). --sub-format "srt" could be replaced with "vtt" or others, depending on what format you prefer (YouTube provides subtitles in WebVTT by default, which yt-dlp can convert to SRT).

After running, yt-dlp will output a file in the current directory, typically named like <video_title>.en.srt or similar. You can then open that file to read the transcript text.

·       **Python usage:** yt-dlp provides a Python interface via yt_dlp.YoutubeDL. You can replicate the above options in a dictionary. For example:

import yt_dlp  
VIDEO_URL = "https://www.youtube.com/watch?v=S-9_AHRq-LI"  
ydl_opts = {  
    "skip_download": True,  
    "writesubtitles": True,  
    "writeautomaticsub": True,  
    "subtitleslangs": ["en"],  
    "subtitlesformat": "vtt",    # or "srt"  
    "quiet": True,               # run quietly  
    "no_warnings": True  
}  
with yt_dlp.YoutubeDL(ydl_opts) as ydl:  
    info = ydl.extract_info(VIDEO_URL, download=True)

In this example, we set options to download subtitles (including auto subs) in English and skip the video. When extract_info(..., download=True) runs, yt-dlp will fetch the subtitles and save them to disk (since writesubtitles is True)[[16]](https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/#:~:text=def%20download_subtitles%28%29%3A%20ydl_opts%20%3D%20,True%2C)[[17]](https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/#:~:text=print%28f,Subtitles%20downloaded%20for%3A%20%7Btitle%7D%20%28%7Bvid). The returned info dict will contain metadata; notably you can check info.get("subtitles") and info.get("automatic_captions") for details of available subtitles[[18]](https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/#:~:text=print%28f). However, the actual subtitle text is not directly in the info object – it’s in the file you just saved.

After this, you can open the .vtt or .srt file that was saved and read the contents in Python. For instance:

import glob  
files = glob.glob("*.en.vtt")  
if files:  
    with open(files[0], 'r', encoding='utf-8') as f:  
        vtt_text = f.read()  
        # You could convert VTT to plain text, or use a library to parse it.

Alternatively, you could specify an output filename in ydl_opts (using the outtmpl option) to know exactly where the file will be. Yt-dlp also supports a "format":"json" for subtitles, but it typically still writes to a file. In most cases, working with the saved SRT/VTT is simplest.

- **Advantages of yt-dlp:** It’s very robust and supports YouTube’s subtitling system fully. It can download **all** subtitles at once (if you specify subtitleslangs = ["all"] it will grab every available language track). It’s also useful for **age-restricted or login-required videos**, because you can provide cookies or OAuth to yt-dlp to access those. For example, using --cookies-from-browser or the programmatic equivalent can let yt-dlp appear as a logged-in user[[19]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=There%20are%20people%20that%20post,hundreds%20of%20videos%20a%20day). This goes beyond what the above two libraries offer (they currently can’t handle age-restricted videos due to YouTube’s restrictions).
- **Caveats:** Yt-dlp is a heavier dependency and using it for just transcripts might be overkill if you don’t need its other features. It will also save files by design, so you’ll need to manage those files (cleanup if needed). That said, it’s a well-maintained solution. Just like other methods, when scraping many videos you should pace your requests to avoid being blocked by YouTube.

## Avoiding Rate Limits and IP Blocks

When using any unofficial method to scrape transcripts, you must be mindful of YouTube’s **rate limiting and bot-detection mechanisms**. There’s no published hard limit for “how many transcripts per minute” you can fetch, but anecdotal evidence and best practices suggest a cautious approach:

- **Insert delays between requests:** A common strategy is to sleep for a few seconds between fetching transcripts. Many developers have found that a **10-second pause** between video requests is a safe minimum to avoid triggering YouTube’s anti-scraping measures[[20]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=and%20yt,out%20of%20trouble%20with%20youtube). For example, one user reports that a 10s delay allowed them to download subtitles for hundreds of videos in playlists without issue[[20]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=and%20yt,out%20of%20trouble%20with%20youtube). Others choose ~20s to be extra safe, especially if they previously hit a block[[21]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=I%20genuinely%20believe%20a%2010,recommending%20a%20risky%20low%20number)[[20]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=and%20yt,out%20of%20trouble%20with%20youtube). In short, **do not bombard the API** – throttle your requests.
- **Randomize or jitter the sleep interval:** Instead of a fixed delay, you can vary it slightly (e.g. sleep 6-12 seconds randomly). This makes traffic appear more human-like. Yt-dlp even has built-in options --min-sleep-interval and --max-sleep-interval for this purpose[[22]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=For%20example%2C%20if%20you%20use%3A)[[20]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=and%20yt,out%20of%20trouble%20with%20youtube). A random delay between requests (say 1–3 seconds for light use, or 10–20 seconds for heavy use) is recommended[[23]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=match%20at%20L565%20,uniform%281%2C%203)[[24]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=,generated%20captions%20for%20better%20readability).
- **Handle errors and respect limits:** If you do trigger a rate limit, YouTube might respond with HTTP 429 (Too Many Requests) or temporarily block your IP. In such cases, your code should catch the exception and **back off**. The youtube-transcript-api will raise a RequestBlocked or IpBlocked exception if it detects this. A robust approach is to catch these and implement an exponential backoff (wait longer and retry). In practice, hitting a hard rate limit might result in needing to stop for some hours. It’s best to avoid getting to that point by pacing yourself upfront. As a rule of thumb: **“Always add delays between requests to avoid rate limits, handle errors gracefully, and remember that not every video has captions”**[[24]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=,generated%20captions%20for%20better%20readability).
- **Use proxies for high-volume scraping:** If you plan to scrape **large batches** of transcripts (e.g. thousands of videos) or run your code on cloud servers, you may need proxies to prevent IP bans. YouTube tends to distrust cloud data center IPs, often blocking them quickly[[11]](https://github.com/jdepoix/youtube-transcript-api#:~:text=Unfortunately%2C%20YouTube%20has%20started%20blocking,is%20the%20most%20reliable%20option). For example, a developer noted their transcript requests worked locally but failed on an AWS VM until they used a proxy[[25]](https://shekhargulati.com/2025/01/05/using-a-tor-proxy-to-bypass-ip-restrictions/#:~:text=Yesterday%20I%20was%20working%20on,VM%20it%20started%20giving%20error)[[26]](https://shekhargulati.com/2025/01/05/using-a-tor-proxy-to-bypass-ip-restrictions/#:~:text=As%20described%20in%20the%20GitHub,blocked%20by%20services%20like%20YouTube). One free strategy is using the Tor network (as a SOCKS proxy) to rotate exit IPs[[26]](https://shekhargulati.com/2025/01/05/using-a-tor-proxy-to-bypass-ip-restrictions/#:~:text=As%20described%20in%20the%20GitHub,blocked%20by%20services%20like%20YouTube), or you can use paid residential proxy services for reliability[[27]](https://github.com/jdepoix/youtube-transcript-api#:~:text=will%20most%20likely%20run%20into,is%20the%20most%20reliable%20option). The youtube-transcript-api library has convenient support for rotating **Webshare** residential proxies built-in, precisely to address this issue[[11]](https://github.com/jdepoix/youtube-transcript-api#:~:text=Unfortunately%2C%20YouTube%20has%20started%20blocking,is%20the%20most%20reliable%20option)[[28]](https://github.com/jdepoix/youtube-transcript-api#:~:text=after%20extended%20use%2C%20going%20for,is%20the%20most%20reliable%20option). The idea is to distribute requests across different IP addresses if one IP is doing too much work. **Note:** If you’re just doing personal, moderate use (e.g. a few transcripts per day), you likely **don’t** need proxies – just don’t spam requests. Proxies are a fallback for scale.
- **Login or cookie-based access:** If dealing with age-restricted videos (which require a YouTube account login to view), no amount of delay will help because the transcript is blocked without authentication. In such cases, tools like yt-dlp allow using your account’s cookies to authenticate[[19]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=There%20are%20people%20that%20post,hundreds%20of%20videos%20a%20day). This is an advanced scenario; if your app needs to handle those, you would export cookies from your browser and supply them to yt-dlp. For most public videos, this isn’t necessary.

**In summary**, start with the simplest method (e.g. try youtube-transcript-api first for its simplicity) and see if it meets your needs. It can retrieve transcripts for most public videos quickly and in parsed form. If you run into limitations (IP blocks on a server or need more features), consider switching to or integrating fallback methods like Pytube or yt-dlp. Always incorporate some delay between requests – for example, a loop that fetches transcripts should use something like time.sleep(10) each iteration – to stay under the radar[[29]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=Google%27s%20bot%20detection%20algorithm%20is,From%20the%20help%20text)[[30]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=Working%20around%20rate%20limits%20and,blocks). And if you ever plan to scale up to bulk transcript scraping, be prepared to use rotating IPs or proxies[[24]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=,generated%20captions%20for%20better%20readability)[[27]](https://github.com/jdepoix/youtube-transcript-api#:~:text=will%20most%20likely%20run%20into,is%20the%20most%20reliable%20option) for uninterrupted operation. By following these practices, you can safely leverage free tools to get YouTube transcripts without incurring API costs.

**Sources:** The information above is based on official documentation and user experiences. The youtube-transcript-api documentation and community notes highlight its usage and proxy support[[4]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=video_id%20%3D%20%22dQw4w9WgXcQ%22%20%20,get_transcript%28video_id)[[11]](https://github.com/jdepoix/youtube-transcript-api#:~:text=Unfortunately%2C%20YouTube%20has%20started%20blocking,is%20the%20most%20reliable%20option). Pytube’s documentation demonstrates caption retrieval and conversion to text[[31]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=Pytube%20exposes%20the%20caption%20tracks,a%20video%20that%20contains%20them)[[15]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=%3E%3E%3E%20print%28caption.generate_srt_captions%28%29%29%201%20000%3A000%3A00%2C000%20,dont%20know%20what%20to%20type). Examples from a data scraping guide and Reddit provide guidance on using yt-dlp for subtitles and recommend delays (~10 seconds) to avoid bans[[16]](https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/#:~:text=def%20download_subtitles%28%29%3A%20ydl_opts%20%3D%20,True%2C)[[20]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=and%20yt,out%20of%20trouble%20with%20youtube). Best-practice tips for rate limiting and avoiding blocks are summarized from scraping blogs[[24]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=,generated%20captions%20for%20better%20readability) and developer anecdotes[[26]](https://shekhargulati.com/2025/01/05/using-a-tor-proxy-to-bypass-ip-restrictions/#:~:text=As%20described%20in%20the%20GitHub,blocked%20by%20services%20like%20YouTube). All these sources reinforce the approach of using unofficial APIs carefully to reliably get YouTube transcripts for free.

---

[[1]](https://scrapecreators.com/blog/unofficial-youtube-api#:~:text=YouTube%20can%20supercharge%20your%20content,with%20a%20sleek%20REST%20interface) [[2]](https://scrapecreators.com/blog/unofficial-youtube-api#:~:text=While%20the%20official%20YouTube%20API,JSON%2C%20ready%20for%20your%20workflows) Unlock YouTube Insights with Scrape Creators Unofficial API, Fast, Flexible, and Feature Rich | ScrapeCreators Blog

[https://scrapecreators.com/blog/unofficial-youtube-api](https://scrapecreators.com/blog/unofficial-youtube-api)

[[3]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=Python%27s%20%60youtube,of%20all%2C%20it%27s%20actively%20maintained) [[4]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=video_id%20%3D%20%22dQw4w9WgXcQ%22%20%20,get_transcript%28video_id) [[6]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=video_id%20%3D%20) [[7]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=for%20transcript%20in%20transcript_list%3A%20print%28f,print) [[23]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=match%20at%20L565%20,uniform%281%2C%203) [[24]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=,generated%20captions%20for%20better%20readability) [[30]](https://roundproxies.com/blog/scrape-youtube-captions/#:~:text=Working%20around%20rate%20limits%20and,blocks) How to Scrape Captions from YouTube

[https://roundproxies.com/blog/scrape-youtube-captions/](https://roundproxies.com/blog/scrape-youtube-captions/)

[[5]](https://github.com/jdepoix/youtube-transcript-api#:~:text=By%20default%20this%20module%20always,in%20the%20requested%20language%20is) [[8]](https://github.com/jdepoix/youtube-transcript-api#:~:text=transcript%20%3D%20transcript_list.find_transcript%28,fetch) [[9]](https://github.com/jdepoix/youtube-transcript-api#:~:text=Formatters%20are%20meant%20to%20be,separated%20format%20%28%60.csv%60%29%2C%20etc) [[10]](https://github.com/jdepoix/youtube-transcript-api#:~:text=,SRTFormatter) [[11]](https://github.com/jdepoix/youtube-transcript-api#:~:text=Unfortunately%2C%20YouTube%20has%20started%20blocking,is%20the%20most%20reliable%20option) [[27]](https://github.com/jdepoix/youtube-transcript-api#:~:text=will%20most%20likely%20run%20into,is%20the%20most%20reliable%20option) [[28]](https://github.com/jdepoix/youtube-transcript-api#:~:text=after%20extended%20use%2C%20going%20for,is%20the%20most%20reliable%20option) GitHub - jdepoix/youtube-transcript-api: This is a python API which allows you to get the transcript/subtitles for a given YouTube video. It also works for automatically generated subtitles and it does not require an API key nor a headless browser, like other selenium based solutions do!

[https://github.com/jdepoix/youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)

[[12]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=Subtitle%2FCaption%20Tracks%C2%B6) [[13]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=,el) [[14]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=%3E%3E%3E%20caption.xml_captions%20%27%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22utf,39) [[15]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=%3E%3E%3E%20print%28caption.generate_srt_captions%28%29%29%201%20000%3A000%3A00%2C000%20,dont%20know%20what%20to%20type) [[31]](https://pytube3.readthedocs.io/en/latest/user/quickstart.html#:~:text=Pytube%20exposes%20the%20caption%20tracks,a%20video%20that%20contains%20them) Quickstart — pytube3 9.6.4 documentation

[https://pytube3.readthedocs.io/en/latest/user/quickstart.html](https://pytube3.readthedocs.io/en/latest/user/quickstart.html)

[[16]](https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/#:~:text=def%20download_subtitles%28%29%3A%20ydl_opts%20%3D%20,True%2C) [[17]](https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/#:~:text=print%28f,Subtitles%20downloaded%20for%3A%20%7Btitle%7D%20%28%7Bvid) [[18]](https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/#:~:text=print%28f) How to scrape YouTube video content with Python - Residential proxies - DataImpulse

[https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/](https://dataimpulse.com/blog/how-to-scrape-youtube-video-content-with-python/)

[[19]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=There%20are%20people%20that%20post,hundreds%20of%20videos%20a%20day) [[20]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=and%20yt,out%20of%20trouble%20with%20youtube) [[21]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=I%20genuinely%20believe%20a%2010,recommending%20a%20risky%20low%20number) [[22]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=For%20example%2C%20if%20you%20use%3A) [[29]](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/#:~:text=Google%27s%20bot%20detection%20algorithm%20is,From%20the%20help%20text) Rate Limiting for downloading transcripts/subtitles? : r/youtubedl

[https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/](https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/)

[[25]](https://shekhargulati.com/2025/01/05/using-a-tor-proxy-to-bypass-ip-restrictions/#:~:text=Yesterday%20I%20was%20working%20on,VM%20it%20started%20giving%20error) [[26]](https://shekhargulati.com/2025/01/05/using-a-tor-proxy-to-bypass-ip-restrictions/#:~:text=As%20described%20in%20the%20GitHub,blocked%20by%20services%20like%20YouTube) Using a Tor proxy to bypass IP restrictions – Shekhar Gulati

[https://shekhargulati.com/2025/01/05/using-a-tor-proxy-to-bypass-ip-restrictions/](https://shekhargulati.com/2025/01/05/using-a-tor-proxy-to-bypass-ip-restrictions/)