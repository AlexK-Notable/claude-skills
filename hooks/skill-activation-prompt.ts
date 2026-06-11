#!/usr/bin/env node
import { readFileSync } from 'fs';
import { join } from 'path';

interface HookInput {
    session_id: string;
    transcript_path: string;
    cwd: string;
    permission_mode: string;
    prompt: string;
}

interface PromptTriggers {
    keywords?: string[];
    intentPatterns?: string[];
}

interface SkillRule {
    type: 'guardrail' | 'domain';
    enforcement: 'block' | 'suggest' | 'warn';
    priority: 'critical' | 'high' | 'medium' | 'low';
    promptTriggers?: PromptTriggers;
}

interface SkillRules {
    version: string;
    skills: Record<string, SkillRule>;
}

interface MatchedSkill {
    name: string;
    matchType: 'keyword' | 'intent';
    config: SkillRule;
}

// Debug logging is opt-in: this hook runs on EVERY prompt, so by default any
// internal error must produce NO output and exit 0 (never noise, never block).
const DEBUG = process.env.SKILL_HOOK_DEBUG === '1';

function debugLog(...args: unknown[]) {
    if (DEBUG) {
        console.error(...args);
    }
}

function escapeRegExp(s: string): string {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Keyword matching: short keywords (< 5 chars, e.g. "bw", "age") match far too
// many substrings ("bwrap", "page"), so they require word boundaries. Longer
// keywords/phrases keep plain substring matching.
function keywordMatches(prompt: string, keyword: string): boolean {
    const kw = keyword.toLowerCase();
    if (kw.length >= 5) {
        return prompt.includes(kw);
    }
    try {
        return new RegExp(`\\b${escapeRegExp(kw)}\\b`).test(prompt);
    } catch {
        return prompt.includes(kw);
    }
}

async function main() {
    try {
        // Read input from stdin
        const input = readFileSync(0, 'utf-8');
        const data: HookInput = JSON.parse(input);
        const prompt = data.prompt.toLowerCase();

        // Load skill rules
        // Try project-specific first, then fall back to global
        const homeDir = process.env.HOME || require('os').homedir();
        const projectDir = process.env.CLAUDE_PROJECT_DIR;

        let rulesPath: string;
        let rules: SkillRules;

        // Try project-specific location first
        if (projectDir) {
            const projectRulesPath = join(projectDir, '.claude', 'skills', 'skill-rules.json');
            try {
                rules = JSON.parse(readFileSync(projectRulesPath, 'utf-8'));
                rulesPath = projectRulesPath;
            } catch {
                // Fall back to global
                rulesPath = join(homeDir, '.claude', 'skills', 'skill-rules.json');
                rules = JSON.parse(readFileSync(rulesPath, 'utf-8'));
            }
        } else {
            // No project dir, use global
            rulesPath = join(homeDir, '.claude', 'skills', 'skill-rules.json');
            rules = JSON.parse(readFileSync(rulesPath, 'utf-8'));
        }

        const matchedSkills: MatchedSkill[] = [];

        // Check each skill for matches
        for (const [skillName, config] of Object.entries(rules.skills)) {
            const triggers = config.promptTriggers;
            if (!triggers) {
                continue;
            }

            // Keyword matching
            if (triggers.keywords) {
                const keywordMatch = triggers.keywords.some(kw => keywordMatches(prompt, kw));
                if (keywordMatch) {
                    matchedSkills.push({ name: skillName, matchType: 'keyword', config });
                    continue;
                }
            }

            // Intent pattern matching — compile each pattern in its own
            // try/catch so one malformed regex in skill-rules.json skips
            // only itself, not the whole matching loop.
            if (triggers.intentPatterns) {
                const intentMatch = triggers.intentPatterns.some(pattern => {
                    try {
                        return new RegExp(pattern, 'i').test(prompt);
                    } catch (err) {
                        debugLog(`skill-activation-prompt: skipping malformed intentPattern for "${skillName}": ${pattern}`, err);
                        return false;
                    }
                });
                if (intentMatch) {
                    matchedSkills.push({ name: skillName, matchType: 'intent', config });
                }
            }
        }

        // Generate output if matches found
        if (matchedSkills.length > 0) {
            let output = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
            output += '🎯 SKILL ACTIVATION CHECK\n';
            output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';

            // Group by priority
            const critical = matchedSkills.filter(s => s.config.priority === 'critical');
            const high = matchedSkills.filter(s => s.config.priority === 'high');
            const medium = matchedSkills.filter(s => s.config.priority === 'medium');
            const low = matchedSkills.filter(s => s.config.priority === 'low');

            if (critical.length > 0) {
                output += '⚠️ CRITICAL SKILLS (REQUIRED):\n';
                critical.forEach(s => output += `  → ${s.name}\n`);
                output += '\n';
            }

            if (high.length > 0) {
                output += '📚 RECOMMENDED SKILLS:\n';
                high.forEach(s => output += `  → ${s.name}\n`);
                output += '\n';
            }

            if (medium.length > 0) {
                output += '💡 SUGGESTED SKILLS:\n';
                medium.forEach(s => output += `  → ${s.name}\n`);
                output += '\n';
            }

            if (low.length > 0) {
                output += '📌 OPTIONAL SKILLS:\n';
                low.forEach(s => output += `  → ${s.name}\n`);
                output += '\n';
            }

            output += 'ACTION: Use Skill tool BEFORE responding\n';
            output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';

            console.log(output);
        }

        process.exit(0);
    } catch (err) {
        // Never fail the prompt: print nothing (unless SKILL_HOOK_DEBUG=1)
        // and exit 0. A broken hook must be invisible, not noisy.
        debugLog('Error in skill-activation-prompt hook:', err);
        process.exit(0);
    }
}

main().catch(err => {
    debugLog('Uncaught error in skill-activation-prompt hook:', err);
    process.exit(0);
});
