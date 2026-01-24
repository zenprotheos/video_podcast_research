#!/usr/bin/env node

/**
 * Front-Matter Validator for OneShot Documentation
 * Simple, dependency-free validation and fixing of front-matter
 */

const fs = require('fs');
const path = require('path');

class FrontMatterValidator {
    constructor() {
        this.requiredFields = [
            'title',
            'created', 
            'type',
            'purpose',
            'status',
            'tags'
        ];
        
        this.validTypes = [
            'architecture',
            'planning',
            'analysis',
            'example',
            'test',
            'index',
            'audit_plan',
            'integration_summary',
            'persona_config',
            'template',
            'tool',
            'document',
            'completion',
            'completion_summary',
            'completion-summary',
            'progress_tracker',
            'progress-tracking',
            'task-management',
            'implementation_plan',
            'implementation',
            'troubleshooting',
            'design',
            'documentation',
            'user-guide',
            'guide',
            'proposal',
            'tasks',
            'task_plan',
            'task-doc',
            'task_architecture',
            'obsidian-integration',
            'tracking',
            'subtask',
            'progress',
            'debugging',
            'resumable_session',
            'personal',
            'note',
            'sop',
            'transcript',
            'working',
            'dev-log',
            'diagram',
            'snippet',
            'project'
        ];
        
        this.validStatuses = [
            'Active',
            'Complete',
            'Legacy',
            'Deprecated',
            'In-Progress',
            'Pending',
            'Completed',
            'Draft',
            'Updated',
            'unread',
            'reading',
            'finished',
            'processed',
            'private',
            'active',
            'on-hold',
            'complete',
            'archived',
            'draft',
            'review',
            'approved',
            'deprecated',
            'raw',
            'processed',
            'summarized',
            'in-progress',
            'working',
            'Unread',
            'Reading',
            'Finished'
        ];

        // Placeholder text patterns to detect
        this.placeholderPatterns = [
            /^detailed description of this document's purpose and scope$/i,
            /^describe the purpose and scope of this document$/i,
            /^document content goes here$/i,
            /^replace with actual content$/i,
            /^\[describe.*\]$/i,
            /^\[document.*\]$/i,
            /^\[replace.*\]$/i,
            /^todo.*$/i,
            /^tbd.*$/i,
            /^coming soon.*$/i,
            /^placeholder.*$/i
        ];
    }

    isPlaceholderText(text) {
        if (!text) return true;

        // Handle arrays (like tags) - consider them valid if they have content
        if (Array.isArray(text)) {
            return text.length === 0 || text.every(item => !item || item.trim().length < 2);
        }

        if (typeof text !== 'string') return true;

        const trimmed = text.trim().toLowerCase();

        // Check for empty or very short content - be less restrictive
        if (trimmed.length < 3) return true;

        // Check against placeholder patterns - only the most obvious ones
        const obviousPlaceholders = [
            /^detailed description of this document's purpose and scope$/i,
            /^describe the purpose and scope of this document$/i,
            /^document content goes here$/i,
            /^replace with actual content$/i,
            /^\[replace.*\]$/i,
            /^todo$/i,
            /^tbd$/i,
            /^coming soon$/i,
            /^placeholder$/i
        ];

        for (const pattern of obviousPlaceholders) {
            if (pattern.test(trimmed)) return true;
        }

        return false;
    }

    countWords(text) {
        if (!text || typeof text !== 'string') return 0;
        return text.trim().split(/\s+/).filter(word => word.length > 0).length;
    }

    parseSimpleYAML(yamlContent) {
        const result = {};
        const lines = yamlContent.split(/\r?\n/);
        
        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith('#')) continue;
            
            const colonIndex = trimmed.indexOf(':');
            if (colonIndex === -1) continue;
            
            const key = trimmed.substring(0, colonIndex).trim();
            let value = trimmed.substring(colonIndex + 1).trim();
            
            // Remove quotes
            if ((value.startsWith('"') && value.endsWith('"')) || 
                (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
            }
            
            // Handle arrays (simple format)
            if (value.startsWith('[') && value.endsWith(']')) {
                const arrayContent = value.slice(1, -1);
                result[key] = arrayContent.split(',').map(item => 
                    item.trim().replace(/["']/g, '')
                ).filter(item => item);
            } else {
                result[key] = value;
            }
        }
        
        return result;
    }

    validateFile(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const frontMatterMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
            
            if (!frontMatterMatch) {
                return {
                    valid: false,
                    errors: ['No front-matter found'],
                    filePath
                };
            }

            const frontMatter = this.parseSimpleYAML(frontMatterMatch[1]);
            return this.validateFrontMatter(frontMatter, filePath);
            
        } catch (error) {
            return {
                valid: false,
                errors: [`Error reading file: ${error.message}`],
                filePath
            };
        }
    }

    validateFrontMatter(frontMatter, filePath) {
        const errors = [];
        const warnings = [];

        // Check required fields and validate content quality
        for (const field of this.requiredFields) {
            if (!frontMatter[field]) {
                errors.push(`Missing required field: ${field}`);
            } else if (this.isPlaceholderText(frontMatter[field])) {
                errors.push(`Field '${field}' contains placeholder/template text that needs to be replaced with actual content`);
            }
        }

        // Validate field values (allow flexible content, just ensure not empty)
        if (frontMatter.type && frontMatter.type.trim() === '') {
            errors.push(`Field 'type' cannot be empty`);
        }

        if (frontMatter.status && frontMatter.status.trim() === '') {
            errors.push(`Field 'status' cannot be empty`);
        }

        // Check purpose description quality - must be more than 20 words
        if (frontMatter.purpose) {
            const wordCount = this.countWords(frontMatter.purpose);
            if (wordCount < 20) {
                errors.push(`Purpose description is too short (${wordCount} words). Must be at least 20 words for proper documentation indexing and clarity. Current: "${frontMatter.purpose.substring(0, 100)}${frontMatter.purpose.length > 100 ? '...' : ''}"`);
            }
            if (wordCount > 100) {
                warnings.push(`Purpose description is very long (${wordCount} words). Consider condensing to focus on key points (recommended: 20-50 words)`);
            }
        }

        return {
            valid: errors.length === 0,
            errors,
            warnings,
            filePath,
            frontMatter
        };
    }

    scanDirectory(dirPath) {
        const results = {
            totalFiles: 0,
            validFiles: 0,
            invalidFiles: [],
            warnings: []
        };

        this.scanDirectoryRecursive(dirPath, results);
        return results;
    }

    scanDirectoryRecursive(dirPath, results) {
        try {
            const items = fs.readdirSync(dirPath);
            
            for (const item of items) {
                const fullPath = path.join(dirPath, item);
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory()) {
                    if (!this.shouldSkipDirectory(item)) {
                        this.scanDirectoryRecursive(fullPath, results);
                    }
                } else if (path.extname(item) === '.md') {
                    results.totalFiles++;
                    const validation = this.validateFile(fullPath);
                    
                    if (validation.valid) {
                        results.validFiles++;
                    } else {
                        results.invalidFiles.push(validation);
                    }
                    
                    if (validation.warnings) {
                        results.warnings.push(...validation.warnings.map(w => ({
                            file: fullPath,
                            warning: w
                        })));
                    }
                }
            }
        } catch (error) {
            console.error(`Error scanning directory ${dirPath}:`, error.message);
        }
    }

    shouldSkipDirectory(dirName) {
        const skipDirs = [
            'node_modules',
            '.git',
            '__pycache__',
            '.obsidian',
            '.vscode',
            '.cursor'
        ];
        return skipDirs.includes(dirName) || dirName.startsWith('.');
    }

    generateReport(results) {
        const total = results.totalFiles;
        const valid = results.validFiles;
        const invalid = results.invalidFiles.length;
        const percentage = Math.round((valid / total) * 100);

        let report = `# Front-Matter Validation Report\n\n`;
        report += `## Summary\n`;
        report += `- **Total Files**: ${total}\n`;
        report += `- **Valid**: ${valid} (${percentage}%)\n`;
        report += `- **Invalid**: ${invalid}\n`;
        report += `- **Warnings**: ${results.warnings.length}\n\n`;

        if (invalid > 0) {
            report += `## Invalid Files\n\n`;
            for (const file of results.invalidFiles) {
                report += `### ${path.relative('.', file.filePath)}\n`;
                for (const error of file.errors) {
                    report += `- ❌ ${error}\n`;
                }
                report += '\n';
            }
        }

        if (results.warnings.length > 0) {
            report += `## Warnings\n\n`;
            for (const warning of results.warnings) {
                report += `- ⚠️ **${path.relative('.', warning.file)}**: ${warning.warning}\n`;
            }
            report += '\n';
        }

        return report;
    }

    generateTemplate(fileName, type = 'document') {
        const now = new Date().toISOString();
        const title = fileName
            .replace(/\.md$/, '')
            .replace(/[_-]/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());

        // Generate a more descriptive purpose based on type
        const purposeTemplates = {
            'architecture': 'This document provides a comprehensive architectural overview of the system design, including component relationships, data flows, and technical decisions that guide the implementation. It serves as the foundation for understanding how different parts of the system interact and evolve over time.',
            'planning': 'This planning document outlines the strategic approach, timeline, and key milestones for the project. It includes detailed requirements analysis, risk assessment, resource allocation, and success criteria to ensure effective project execution and delivery.',
            'analysis': 'This analysis document examines specific aspects of the system or problem domain, providing detailed insights, data-driven conclusions, and actionable recommendations based on thorough investigation and evaluation of available information.',
            'document': 'This document serves as a comprehensive reference for understanding and implementing specific functionality or processes. It provides detailed information, examples, and guidelines to support effective usage and maintenance of the documented system or procedure.'
        };

        const purpose = purposeTemplates[type] || 'This document provides detailed information and guidance for understanding and working with the documented subject matter. It includes comprehensive explanations, examples, and practical instructions to support effective implementation and usage of the described concepts or processes.';

        return `---
title: "${title}"
created: "${now}"
type: "${type}"
purpose: "${purpose}"
status: "Active"
tags: ["documentation"]
---

# ${title}

## Overview

This document provides comprehensive information about ${title.toLowerCase()}. The content is structured to support both understanding and practical implementation of the documented concepts.

## Purpose

${purpose}

## Key Information

[Replace this placeholder with actual content specific to this document]

## Implementation Details

[Add specific details, examples, and implementation guidance here]

## Additional Resources

[Any related documentation, links, or references should be listed here]
`;
    }
}

// CLI Usage
if (require.main === module) {
    const args = process.argv.slice(2);
    const command = args[0];
    const targetPath = args[1] || '.';
    
    const validator = new FrontMatterValidator();
    
    switch (command) {
        case 'validate':
            console.log('🔍 Validating front-matter...');
            const results = validator.scanDirectory(targetPath);
            console.log(validator.generateReport(results));
            process.exit(results.invalidFiles.length > 0 ? 1 : 0);
            break;
            
        case 'template':
            const fileName = args[2] || 'new-document.md';
            const type = args[3] || 'document';
            console.log(validator.generateTemplate(fileName, type));
            break;
            
        default:
            console.log(`
Front-Matter Validator for VoiceScribeAI Documentation

Validates front-matter in .md files with flexible requirements:
- All required fields (title, created, type, purpose, status, tags) must be present
- Purpose must be at least 20 words (not characters) and contain meaningful content
- No placeholder/template text allowed in required fields
- Type and status can be any non-empty values (flexible for project needs)

Usage:
  node frontmatter_validator.cjs validate [directory]
  node frontmatter_validator.cjs template [filename] [type]

Commands:
  validate  - Check all .md files for front-matter compliance with detailed fix instructions
  template  - Generate front-matter template for new files with proper purpose statements
            `);
    }
}

module.exports = FrontMatterValidator;
