/**
 * Profile Format Transformer
 * 
 * Utility functions for normalizing profile data between legacy format
 * (executive_summary, psychological_profile, etc.) and new sections-based format.
 * 
 * @module utils/profileTransformer
 */

/**
 * Detects if a profile is in legacy format
 * @param {Object} profileData - Profile data object
 * @returns {boolean} True if legacy format
 */
export const isLegacyFormat = (profileData) => {
    if (!profileData || typeof profileData !== 'object') return false;

    const legacyKeys = [
        'executive_summary',
        'psychological_profile',
        'behavioral_patterns',
        'motivation_matrix',
        'growth_trajectory'
    ];

    const hasLegacyKeys = legacyKeys.some(key => key in profileData);
    const hasNewFormat = 'sections' in profileData && Array.isArray(profileData.sections);

    return hasLegacyKeys && !hasNewFormat;
};

/**
 * Detects if a profile is in new sections format
 * @param {Object} profileData - Profile data object
 * @returns {boolean} True if sections format
 */
export const isSectionsFormat = (profileData) => {
    if (!profileData || typeof profileData !== 'object') return false;
    return 'sections' in profileData && Array.isArray(profileData.sections);
};

/**
 * Transforms legacy format to new sections-based format
 * @param {Object} legacyData - Legacy profile data
 * @returns {Object} Normalized sections-based profile
 */
export const transformLegacyToSections = (legacyData) => {
    const sections = [];

    // Executive Summary
    if (legacyData.executive_summary) {
        sections.push({
            title: 'Executive Summary',
            content: legacyData.executive_summary
        });
    }

    // Psychological Profile
    if (legacyData.psychological_profile) {
        const psych = legacyData.psychological_profile;
        const points = [];

        if (psych.personality_archetype) {
            points.push(`Archetype: ${psych.personality_archetype}`);
        }
        if (psych.core_traits && Array.isArray(psych.core_traits)) {
            points.push(`Core Traits: ${psych.core_traits.join(', ')}`);
        }
        if (psych.mindset_analysis) {
            sections.push({
                title: 'Psychological Profile',
                content: psych.mindset_analysis
            });
        }
        if (points.length > 0) {
            sections.push({
                title: 'Personality Traits',
                points
            });
        }
    }

    // Behavioral Patterns
    if (legacyData.behavioral_patterns) {
        const patterns = legacyData.behavioral_patterns;
        const points = [];

        if (patterns.decision_making) {
            points.push(`Decision Making: ${patterns.decision_making}`);
        }
        if (patterns.risk_tolerance) {
            points.push(`Risk Tolerance: ${patterns.risk_tolerance}`);
        }
        if (patterns.communication_style) {
            points.push(`Communication: ${patterns.communication_style}`);
        }

        if (points.length > 0) {
            sections.push({
                title: 'Behavioral Patterns',
                points
            });
        }
    }

    // Motivation Matrix
    if (legacyData.motivation_matrix) {
        const motivation = legacyData.motivation_matrix;
        const points = [];

        if (motivation.underlying_drivers && Array.isArray(motivation.underlying_drivers)) {
            motivation.underlying_drivers.forEach(driver => {
                points.push(driver);
            });
        }
        if (motivation.success_metrics) {
            points.push(`Success Metrics: ${motivation.success_metrics}`);
        }

        if (points.length > 0) {
            sections.push({
                title: 'Motivation & Drivers',
                points
            });
        }
    }

    // Growth Trajectory
    if (legacyData.growth_trajectory) {
        const growth = legacyData.growth_trajectory;
        const points = [];

        if (growth.current_focus) {
            points.push(`Current Focus: ${growth.current_focus}`);
        }
        if (growth.potential_blind_spots && Array.isArray(growth.potential_blind_spots)) {
            growth.potential_blind_spots.forEach(spot => {
                points.push(`Blind Spot: ${spot}`);
            });
        }
        if (growth.development_areas) {
            points.push(`Development Areas: ${growth.development_areas}`);
        }

        if (points.length > 0) {
            sections.push({
                title: 'Growth Trajectory',
                points
            });
        }
    }

    // Interaction History (for updated profiles)
    if (legacyData.interaction_history) {
        const history = legacyData.interaction_history;
        const points = [];

        if (history.observation_log) {
            points.push(history.observation_log);
        }
        if (history.behavioral_evolution) {
            points.push(`Evolution: ${history.behavioral_evolution}`);
        }

        if (points.length > 0) {
            sections.push({
                title: 'Interaction History',
                points
            });
        }
    }

    return {
        confidence: legacyData.confidence || null,
        sections,
        _transformed: true,
        _originalFormat: 'legacy'
    };
};

/**
 * Normalizes any profile format to sections-based format
 * Main entry point for profile data normalization.
 * 
 * @param {Object|string} profileData - Profile data in any format
 * @returns {Object|null} Normalized profile or null if invalid
 */
export const normalizeProfileData = (profileData) => {
    if (!profileData) return null;

    // If it's a string, check format
    if (typeof profileData === 'string') {
        const trimmed = profileData.trim();

        // Check if it's markdown format (has ### headers)
        if (trimmed.includes('###') || (trimmed.includes('##') && !trimmed.startsWith('{'))) {
            return parseMarkdownProfile(trimmed);
        }

        // Try to parse as JSON
        try {
            profileData = JSON.parse(trimmed);
        } catch (e) {
            // Not JSON and not markdown - return as raw content
            return {
                confidence: null,
                sections: [{
                    title: 'Profile',
                    content: profileData
                }],
                _transformed: true,
                _originalFormat: 'text'
            };
        }
    }

    // Already in sections format
    if (isSectionsFormat(profileData)) {
        return profileData;
    }

    // Legacy format - transform
    if (isLegacyFormat(profileData)) {
        return transformLegacyToSections(profileData);
    }

    // Unknown format - wrap as-is
    return {
        confidence: null,
        sections: [{
            title: 'Profile Data',
            content: JSON.stringify(profileData, null, 2)
        }],
        _transformed: true,
        _originalFormat: 'unknown'
    };
};

/**
 * Parse markdown-style profile into sections
 * Handles sections with paragraphs, bullet points, or mixed content
 * @param {string} text - Markdown text
 * @returns {Object} Sections-based profile
 */
export const parseMarkdownProfile = (text) => {
    const sections = [];
    const lines = text.split('\n');
    let currentSection = null;
    let confidence = null;

    lines.forEach(line => {
        // Check for headers (## or ###)
        if (line.startsWith('###') || line.startsWith('##')) {
            if (currentSection) sections.push(currentSection);
            currentSection = {
                title: line.replace(/^#{2,3}\s*/, '').trim(),
                paragraphs: [],
                points: []
            };
        } else if (line.trim() && currentSection) {
            const trimmedLine = line.trim();

            // Check for bullet points
            if (trimmedLine.startsWith('-') || trimmedLine.startsWith('•') || trimmedLine.startsWith('*')) {
                currentSection.points.push(trimmedLine.replace(/^[-•*]\s*/, '').trim());
            } else {
                // Check for confidence score in text
                const confidenceMatch = trimmedLine.match(/(?:Low|Medium|High)\s*\(?([\d.]+)\)?/i);
                if (confidenceMatch) {
                    confidence = parseFloat(confidenceMatch[1]);
                }
                // Regular paragraph text
                currentSection.paragraphs.push(trimmedLine);
            }
        }
    });

    // Don't forget the last section
    if (currentSection) sections.push(currentSection);

    // Convert to proper section format
    return {
        confidence: confidence,
        sections: sections.map(section => {
            // If section has both paragraphs and points, combine them
            if (section.paragraphs.length > 0 && section.points.length > 0) {
                return {
                    title: section.title,
                    content: section.paragraphs.join('\n'),
                    points: section.points
                };
            }
            // Only points
            if (section.points.length > 0) {
                return {
                    title: section.title,
                    points: section.points
                };
            }
            // Only paragraphs/content
            return {
                title: section.title,
                content: section.paragraphs.join('\n')
            };
        }),
        _transformed: true,
        _originalFormat: 'markdown'
    };
};
