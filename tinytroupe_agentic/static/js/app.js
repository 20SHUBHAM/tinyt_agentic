// Agentic Focus Group System - Frontend JavaScript

class FocusGroupApp {
    constructor() {
        this.currentSessionId = null;
        this.currentPersonas = [];
        this.currentTopic = '';
        this.discussionPollingInterval = null;
        this.currentPlanText = '';
        this.init();
    }

    init() {
        this.bindEvents();
        this.showStep(0);
    }

    bindEvents() {
        // Step 0: Plan Generation
        document.getElementById('generate-plan-btn').addEventListener('click', () => {
            this.generatePlan();
        });

        document.getElementById('accept-plan-btn').addEventListener('click', () => {
            this.acceptPlan();
        });

        // Step 1: Persona Generation
        document.getElementById('persona-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generatePersonas();
        });

        // Step 2: Update Personas
        document.getElementById('update-personas-btn').addEventListener('click', () => {
            this.updatePersonas();
        });

        document.getElementById('start-discussion-btn').addEventListener('click', () => {
            this.startDiscussion();
        });

        // Q&A System
        document.getElementById('ask-question-btn').addEventListener('click', () => {
            this.askQuestion();
        });

        document.getElementById('qa-question').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.askQuestion();
            }
        });

        // Suggested Questions
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggested-question')) {
                document.getElementById('qa-question').value = e.target.textContent;
                this.askQuestion();
            }
        });
    }

    showStep(stepNumber) {
        // Hide all steps
        for (let i = 0; i <= 4; i++) {
            const card = document.getElementById(`step${i}-card`);
            if (card) {
                card.classList.add('d-none');
            }
        }

        // Show current step
        const currentCard = document.getElementById(`step${stepNumber}-card`);
        if (currentCard) {
            currentCard.classList.remove('d-none');
            currentCard.classList.add('fade-in');
        }

        // Update stepper
        for (let i = 0; i <= 4; i++) {
            const indicator = document.getElementById(`step-indicator-${i}`);
            if (indicator) {
                if (i <= stepNumber) indicator.classList.add('active');
                else indicator.classList.remove('active');
            }
        }

        // Scroll to step
        if (stepNumber > 0) {
            currentCard.scrollIntoView({ behavior: 'smooth' });
        }
    }

    showLoading(message = 'Processing...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');
        messageEl.textContent = message;
        overlay.classList.remove('d-none');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('d-none');
    }

    async generatePlan() {
        const brief = document.getElementById('topic-brief').value.trim();
        if (!brief) {
            this.showAlert('Please enter a brief topic description.', 'warning');
            return;
        }
        this.showLoading('Generating discussion plan...');
        try {
            const res = await fetch('/generate-plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic_brief: brief })
            });
            const data = await res.json();
            if (data.success) {
                this.currentSessionId = data.session_id;
                this.currentPlanText = data.plan_text;
                document.getElementById('generated-plan').value = data.plan_text;
                this.showAlert('Plan generated. You can edit it before continuing.', 'success');
            } else {
                this.showAlert('Failed to generate plan.', 'danger');
            }
        } catch (e) {
            console.error(e);
            this.showAlert('Network error while generating plan.', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    async acceptPlan() {
        const planText = document.getElementById('generated-plan').value.trim();
        const topicBrief = document.getElementById('topic-brief').value.trim();
        if (!this.currentSessionId) {
            // If plan not generated yet, generate it first
            await this.generatePlan();
        }
        if (!this.currentSessionId) {
            this.showAlert('Could not create a session for the plan.', 'danger');
            return;
        }
        this.showLoading('Saving plan and moving to personas...');
        try {
            await fetch('/accept-plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.currentSessionId, plan_text: planText, discussion_topic: topicBrief })
            });
            // preload topic into persona form
            document.getElementById('discussion-topic').value = topicBrief;
            this.showStep(1);
        } catch (e) {
            console.error(e);
            this.showAlert('Failed to save plan.', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    async generatePersonas() {
        const contextPrompt = document.getElementById('context-prompt').value;
        const discussionTopic = document.getElementById('discussion-topic').value;

        if (!contextPrompt.trim() || !discussionTopic.trim()) {
            this.showAlert('Please fill in both the context prompt and discussion topic.', 'warning');
            return;
        }

        this.showLoading('Generating personas based on your context...');

        try {
            const response = await fetch('/generate-personas', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    context_prompt: contextPrompt,
                    discussion_topic: discussionTopic,
                    session_id: this.currentSessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentSessionId = data.session_id;
                this.currentPersonas = data.personas;
                this.currentTopic = data.topic;
                
                this.displayPersonas(data.personas, data.topic);
                this.showStep(2);
                this.showAlert('Personas generated successfully! Review and edit if needed.', 'success');
            } else {
                this.showAlert('Error generating personas. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Network error. Please check your connection and try again.', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    displayPersonas(personas, topic) {
        const container = document.getElementById('personas-container');
        const topicInput = document.getElementById('edit-topic');
        
        topicInput.value = topic;
        
        let html = '<div class="row">';
        
        personas.forEach((persona, index) => {
            html += `
                <div class="col-md-6 mb-3">
                    <div class="persona-card">
                        <div class="persona-header">
                            <h5 class="mb-0">
                                <i class="fas fa-user me-2"></i>
                                <input type="text" class="form-control persona-name bg-transparent border-0 text-white fw-bold" 
                                       data-index="${index}" value="${persona.name}" 
                                       style="background: transparent !important; color: white !important;">
                            </h5>
                        </div>
                        <div class="persona-body">
                            <div class="row mb-3">
                                <div class="col-6">
                                    <label class="form-label"><strong>Age:</strong></label>
                                    <input type="number" class="form-control persona-age" data-index="${index}" 
                                           value="${persona.age}" min="18" max="65">
                                </div>
                                <div class="col-6">
                                    <label class="form-label"><strong>Location:</strong></label>
                                    <input type="text" class="form-control persona-location" data-index="${index}" 
                                           value="${persona.location}">
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label"><strong>Occupation:</strong></label>
                                <input type="text" class="form-control persona-occupation" data-index="${index}" 
                                       value="${persona.occupation}">
                            </div>
                            <div class="mb-3">
                                <label class="form-label"><strong>Monthly Budget:</strong></label>
                                <input type="text" class="form-control persona-budget" data-index="${index}" 
                                       value="${persona.monthly_budget}" placeholder="e.g., ₹2,800 or ₹1,500-3,000">
                            </div>
                            <div class="mb-3">
                                <label class="form-label"><strong>Personality Type:</strong></label>
                                <select class="form-select persona-personality" data-index="${index}">
                                    <option value="enthusiastic" ${persona.personality_type === 'enthusiastic' ? 'selected' : ''}>Enthusiastic</option>
                                    <option value="analytical" ${persona.personality_type === 'analytical' ? 'selected' : ''}>Analytical</option>
                                    <option value="trendy" ${persona.personality_type === 'trendy' ? 'selected' : ''}>Trendy</option>
                                    <option value="cautious" ${persona.personality_type === 'cautious' ? 'selected' : ''}>Cautious</option>
                                    <option value="expert" ${persona.personality_type === 'expert' ? 'selected' : ''}>Expert</option>
                                    <option value="budget_focused" ${persona.personality_type === 'budget_focused' ? 'selected' : ''}>Budget Focused</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label"><strong>Background:</strong></label>
                                <textarea class="form-control persona-background" data-index="${index}" rows="4">${persona.background}</textarea>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    async updatePersonas() {
        if (!this.currentSessionId) {
            this.showAlert('No active session found.', 'danger');
            return;
        }

        this.showLoading('Updating personas and topic...');

        try {
            // Collect updated data
            const updatedTopic = document.getElementById('edit-topic').value;
            const updatedPersonas = [...this.currentPersonas];
            
            // Update all editable fields
            document.querySelectorAll('.persona-name').forEach((input) => {
                const index = parseInt(input.dataset.index);
                updatedPersonas[index].name = input.value;
            });
            
            document.querySelectorAll('.persona-age').forEach((input) => {
                const index = parseInt(input.dataset.index);
                updatedPersonas[index].age = parseInt(input.value) || updatedPersonas[index].age;
            });
            
            document.querySelectorAll('.persona-location').forEach((input) => {
                const index = parseInt(input.dataset.index);
                updatedPersonas[index].location = input.value;
            });
            
            document.querySelectorAll('.persona-occupation').forEach((input) => {
                const index = parseInt(input.dataset.index);
                updatedPersonas[index].occupation = input.value;
            });
            
            document.querySelectorAll('.persona-budget').forEach((input) => {
                const index = parseInt(input.dataset.index);
                updatedPersonas[index].monthly_budget = input.value;
            });
            
            document.querySelectorAll('.persona-personality').forEach((select) => {
                const index = parseInt(select.dataset.index);
                updatedPersonas[index].personality_type = select.value;
            });
            
            document.querySelectorAll('.persona-background').forEach((textarea) => {
                const index = parseInt(textarea.dataset.index);
                updatedPersonas[index].background = textarea.value;
            });

            const response = await fetch('/update-personas', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    personas: updatedPersonas,
                    topic: updatedTopic
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentPersonas = updatedPersonas;
                this.currentTopic = updatedTopic;
                this.showAlert('Personas and topic updated successfully!', 'success');
            } else {
                this.showAlert('Error updating personas. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Network error. Please try again.', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    async startDiscussion() {
        if (!this.currentSessionId) {
            this.showAlert('No active session found.', 'danger');
            return;
        }

        this.showStep(3);
        this.updateDiscussionProgress(10, 'Initializing TinyPersons...');

        try {
            const response = await fetch(`/start-discussion/${this.currentSessionId}`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.startDiscussionPolling();
            } else {
                this.showAlert('Error starting discussion. Please try again.', 'danger');
                this.showStep(2);
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Network error. Please try again.', 'danger');
            this.showStep(2);
        }
    }

    startDiscussionPolling() {
        let progress = 20;
        const statusMessages = [
            'Creating discussion environment...',
            'Participants are joining the discussion...',
            'Discussion phase 1: Opening questions...',
            'Discussion phase 2: Exploring experiences...',
            'Discussion phase 3: Deep dive analysis...',
            'Discussion phase 4: Comparative insights...',
            'Discussion phase 5: Future perspectives...',
            'Wrapping up discussion...',
            'Generating automated summary...',
            'Finalizing results...'
        ];

        let messageIndex = 0;
        
        this.discussionPollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/session-status/${this.currentSessionId}`);
                const data = await response.json();

                if (data.status === 'discussion_completed') {
                    clearInterval(this.discussionPollingInterval);
                    this.updateDiscussionProgress(100, 'Discussion complete! Configure summary...');
                    
                    setTimeout(() => {
                        this.showSummarySchemaWindow();
                    }, 1000);
                    
                } else if (data.status === 'summary_generated') {
                    clearInterval(this.discussionPollingInterval);
                    this.updateDiscussionProgress(100, 'Summary generated! Loading results...');
                    
                    setTimeout(() => {
                        this.loadDiscussionResults();
                    }, 1000);
                    
                } else if (data.status === 'error') {
                    clearInterval(this.discussionPollingInterval);
                    this.showAlert('An error occurred during the discussion. Please try again.', 'danger');
                    this.showStep(2);
                    
                } else {
                    // Update progress
                    progress = Math.min(progress + 8, 90);
                    const message = statusMessages[messageIndex] || 'Discussion in progress...';
                    this.updateDiscussionProgress(progress, message);
                    
                    messageIndex = (messageIndex + 1) % statusMessages.length;
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 3000);
    }

    updateDiscussionProgress(percentage, message) {
        const progressBar = document.querySelector('#step3-card .progress-bar');
        const statusDiv = document.getElementById('discussion-status');
        
        progressBar.style.width = `${percentage}%`;
        statusDiv.innerHTML = `<i class="fas fa-info-circle me-2"></i>${message}`;
    }

    showSummarySchemaWindow() {
        // Create modal for summary schema configuration
        const modalHtml = `
            <div class="modal fade" id="summarySchemaModal" tabindex="-1" aria-labelledby="summarySchemaModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title" id="summarySchemaModalLabel">
                                <i class="fas fa-cog me-2"></i>Configure Summary Schema
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                <strong>Customize Your Summary:</strong> Describe what specific aspects and insights you want to include in the focus group summary. The AI will generate a structured summary based on your requirements.
                            </div>
                            
                            <div class="mb-3">
                                <label for="summarySchema" class="form-label">
                                    <strong>Summary Schema & Requirements</strong>
                                    <small class="text-muted">(Describe what should be included in the summary)</small>
                                </label>
                                <textarea 
                                    class="form-control" 
                                    id="summarySchema" 
                                    rows="8" 
                                    placeholder="Example:&#10;&#10;1. Executive Summary - Key findings and main insights&#10;2. Participant Demographics - Age groups, backgrounds, spending patterns&#10;3. Key Themes - Most discussed topics and consensus areas&#10;4. Purchase Behavior - What drives decisions and barriers&#10;5. Brand Preferences - Mentioned brands and loyalty patterns&#10;6. Digital Behavior - Online vs offline preferences&#10;7. Price Sensitivity - Budget considerations and value perceptions&#10;8. Recommendations - Actionable business insights&#10;9. Quotes - Memorable participant statements&#10;10. Next Steps - Follow-up research suggestions&#10;&#10;Focus on practical business insights that can inform marketing strategy and product development decisions."
                                >${this.getDefaultSummarySchema()}</textarea>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">
                                    <strong>Quick Schema Templates</strong>
                                </label>
                                <div class="d-flex gap-2 flex-wrap">
                                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="focusGroupApp.loadSchemaTemplate('standard')">
                                        <i class="fas fa-file-alt me-1"></i>Standard Business
                                    </button>
                                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="focusGroupApp.loadSchemaTemplate('marketing')">
                                        <i class="fas fa-bullhorn me-1"></i>Marketing Focus
                                    </button>
                                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="focusGroupApp.loadSchemaTemplate('product')">
                                        <i class="fas fa-box me-1"></i>Product Development
                                    </button>
                                    <button type="button" class="btn btn-outline-primary btn-sm" onclick="focusGroupApp.loadSchemaTemplate('academic')">
                                        <i class="fas fa-graduation-cap me-1"></i>Academic Research
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times me-2"></i>Cancel
                            </button>
                            <button type="button" class="btn btn-primary" onclick="focusGroupApp.generateCustomSummary()">
                                <i class="fas fa-magic me-2"></i>Generate Summary
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('summarySchemaModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('summarySchemaModal'));
        modal.show();
    }

    getDefaultSummarySchema() {
        return `1. Objective - Purpose of the focus group and research goals

2. Participants - Demographics, backgrounds, and selection criteria  

3. Key Insights - 3-5 most important findings and themes

4. Supporting Quotes - Representative participant statements with attribution

5. Opportunities & Recommendations - Actionable business strategies

6. Next Steps - Follow-up research and implementation priorities

Focus on practical insights that can inform business decisions and strategy development.`;
    }

    loadSchemaTemplate(templateType) {
        const schemaTextarea = document.getElementById('summarySchema');
        let template = '';
        
        switch(templateType) {
            case 'standard':
                template = this.getDefaultSummarySchema();
                break;
                
            case 'marketing':
                template = `1. Marketing Objective - Campaign goals and target audience insights

2. Consumer Segments - Identified segments and their characteristics

3. Brand Perceptions - How participants view brands and competitors

4. Message Resonance - Which messages and themes connected most

5. Channel Preferences - Preferred communication and media channels

6. Purchase Triggers - What motivates buying decisions

7. Barriers to Purchase - Obstacles and concerns raised

8. Competitive Analysis - Mentions of competitor brands and positioning

9. Creative Insights - Reactions to concepts, visuals, or messaging

10. Campaign Recommendations - Specific marketing strategy suggestions`;
                break;
                
            case 'product':
                template = `1. Product Concept Evaluation - Overall reception and appeal

2. User Needs Analysis - Identified needs and pain points

3. Feature Prioritization - Most desired and least important features

4. Usability Feedback - Ease of use and user experience insights

5. Pricing Sensitivity - Price expectations and value perceptions

6. Competitive Positioning - How product compares to alternatives

7. Target Market Validation - Confirmation of intended audience fit

8. Usage Scenarios - When and how participants would use the product

9. Improvement Opportunities - Suggested enhancements and modifications

10. Development Priorities - Recommended next steps for product team`;
                break;
                
            case 'academic':
                template = `1. Research Questions - How findings address stated research objectives

2. Methodology Notes - Discussion dynamics and participant engagement

3. Thematic Analysis - Emergent themes and patterns identified

4. Theoretical Implications - Connection to existing literature and frameworks

5. Participant Perspectives - Diverse viewpoints and consensus areas

6. Behavioral Observations - Non-verbal cues and interaction patterns

7. Data Saturation - Evidence of theme saturation or need for additional research

8. Limitations - Acknowledged constraints and potential biases

9. Verbatim Evidence - Key quotes supporting major themes

10. Future Research - Recommended follow-up studies and questions`;
                break;
        }
        
        schemaTextarea.value = template;
    }

    async generateCustomSummary() {
        const schema = document.getElementById('summarySchema').value.trim();
        
        if (!schema) {
            this.showAlert('Please provide a summary schema or requirements.', 'warning');
            return;
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('summarySchemaModal'));
        modal.hide();
        
        this.showLoading('Generating custom summary based on your schema...');
        
        try {
            const response = await fetch('/generate-custom-summary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    summary_schema: schema
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Custom summary generated successfully!', 'success');
                this.loadDiscussionResults();
            } else {
                this.showAlert('Error generating custom summary. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Network error. Please try again.', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    async loadDiscussionResults() {
        this.showLoading('Loading discussion results...');

        try {
            const response = await fetch(`/discussion-results/${this.currentSessionId}`);
            const data = await response.json();

            if (data.transcript && data.summary) {
                this.displayResults(data);
                this.showStep(4);
                this.showAlert('Discussion results loaded successfully!', 'success');
            } else {
                this.showAlert('Error loading results. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Network error loading results.', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    displayResults(data) {
        this.displaySummary(data.summary);
        this.displayTranscript(data.transcript);
        this.initializeQA();
    }

    displaySummary(summary) {
        const container = document.getElementById('summary-content');
        
        let html = '';
        
        // Check if this is a custom summary
        if (summary.metadata && summary.metadata.summary_type === 'custom') {
            html += this.displayCustomSummary(summary);
        } else {
            // Display standard 6-section format
            html += this.displayStandardSummary(summary);
        }

        container.innerHTML = html;
    }

    displayStandardSummary(summary) {
        let html = '';
        
        // 1. Objective
        if (summary.objective) {
            html += `
                <div class="summary-section">
                    <h4><i class="fas fa-target me-2"></i>1. Objective</h4>
                    <p>${summary.objective}</p>
                </div>
            `;
        }

        // 2. Participants
        if (summary.participants) {
            html += `
                <div class="summary-section">
                    <h4><i class="fas fa-users me-2"></i>2. Participants</h4>
                    <p><strong>Number & Type:</strong> ${summary.participants.description || `${summary.participants.count} participants`}</p>
                    
                    ${summary.participants.demographics && summary.participants.demographics.personality_distribution ? `
                        <p><strong>Demographics:</strong></p>
                        <ul class="summary-list">
                            ${Object.entries(summary.participants.demographics.personality_distribution)
                                .map(([type, count]) => `<li>${type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${count} participant${count > 1 ? 's' : ''}</li>`).join('')}
                        </ul>
                    ` : ''}
                    
                    ${summary.participants.selection_criteria ? `
                        <p><strong>Selection Criteria:</strong></p>
                        <ul class="summary-list">
                            ${summary.participants.selection_criteria.map(criteria => `<li>${criteria}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            `;
        }

        // 3. Key Insights
        if (summary.key_insights && summary.key_insights.length > 0) {
            html += `
                <div class="summary-section">
                    <h4><i class="fas fa-lightbulb me-2"></i>3. Key Insights</h4>
                    <ul class="summary-list">
                        ${summary.key_insights.map(insight => `<li>${insight}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // 4. Supporting Quotes / Observations
        if (summary.supporting_quotes && summary.supporting_quotes.length > 0) {
            html += `
                <div class="summary-section">
                    <h4><i class="fas fa-quote-left me-2"></i>4. Supporting Quotes / Observations</h4>
                    ${summary.supporting_quotes.map(quote => `
                        <div class="quote-block mb-3 p-3" style="background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 8px;">
                            <p class="mb-1" style="font-style: italic;">${quote.quote}</p>
                            <small class="text-muted">— ${quote.speaker}</small>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // 5. Opportunities & Recommendations
        if (summary.opportunities_recommendations && summary.opportunities_recommendations.length > 0) {
            html += `
                <div class="summary-section">
                    <h4><i class="fas fa-rocket me-2"></i>5. Opportunities & Recommendations</h4>
                    <ul class="summary-list">
                        ${summary.opportunities_recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // 6. Next Steps
        if (summary.next_steps && summary.next_steps.length > 0) {
            html += `
                <div class="summary-section">
                    <h4><i class="fas fa-arrow-right me-2"></i>6. Next Steps</h4>
                    <ul class="summary-list">
                        ${summary.next_steps.map(step => `<li>${step}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        return html;
    }

    displayCustomSummary(summary) {
        let html = '';
        
        // Add custom summary header
        html += `
            <div class="alert alert-success mb-4">
                <i class="fas fa-magic me-2"></i>
                <strong>Custom Summary Generated</strong> - Based on your specific schema requirements
            </div>
        `;
        
        // Display each custom section
        let sectionNumber = 1;
        for (const [key, value] of Object.entries(summary)) {
            // Skip metadata
            if (key === 'metadata') continue;
            
            // Format section title
            const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const icon = this.getSectionIcon(key);
            
            html += `
                <div class="summary-section">
                    <h4><i class="${icon} me-2"></i>${sectionNumber}. ${title}</h4>
                    ${this.formatSectionContent(value)}
                </div>
            `;
            
            sectionNumber++;
        }
        
        return html;
    }

    getSectionIcon(sectionKey) {
        const iconMap = {
            'objective': 'fas fa-target',
            'participants': 'fas fa-users',
            'insights': 'fas fa-lightbulb',
            'quotes': 'fas fa-quote-left',
            'recommendations': 'fas fa-rocket',
            'next_steps': 'fas fa-arrow-right',
            'behavior': 'fas fa-brain',
            'brand': 'fas fa-tag',
            'marketing': 'fas fa-bullhorn',
            'pricing': 'fas fa-dollar-sign'
        };
        
        // Find matching icon based on key content
        for (const [keyword, icon] of Object.entries(iconMap)) {
            if (sectionKey.toLowerCase().includes(keyword)) {
                return icon;
            }
        }
        
        return 'fas fa-file-alt'; // Default icon
    }

    formatSectionContent(content) {
        if (typeof content === 'string') {
            return `<p>${content}</p>`;
        } else if (Array.isArray(content)) {
            if (content.length > 0 && typeof content[0] === 'object' && content[0].quote) {
                // Format quotes
                return content.map(quote => `
                    <div class="quote-block mb-3 p-3" style="background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 8px;">
                        <p class="mb-1" style="font-style: italic;">${quote.quote}</p>
                        <small class="text-muted">— ${quote.speaker}</small>
                    </div>
                `).join('');
            } else {
                // Format as list
                return `
                    <ul class="summary-list">
                        ${content.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                `;
            }
        } else if (typeof content === 'object') {
            // Format object content
            let html = '';
            for (const [key, value] of Object.entries(content)) {
                const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                
                if (Array.isArray(value)) {
                    html += `
                        <h6>${formattedKey}:</h6>
                        <ul class="summary-list">
                            ${value.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    `;
                } else {
                    html += `<p><strong>${formattedKey}:</strong> ${value}</p>`;
                }
            }
            return html;
        } else {
            return `<p>${content}</p>`;
        }
    }

    displayTranscript(transcript) {
        const container = document.getElementById('transcript-content');
        
        let html = '';
        
        transcript.forEach(entry => {
            const entryType = entry.type || 'unknown';
            const speaker = entry.speaker || 'Unknown';
            const content = entry.content || '';
            const timestamp = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : '';
            
            let cssClass = 'transcript-entry';
            let icon = 'fas fa-comment';
            
            if (speaker === 'Moderator') {
                cssClass += ' transcript-moderator';
                icon = 'fas fa-microphone';
            } else if (entryType === 'interaction') {
                cssClass += ' transcript-interaction';
                icon = 'fas fa-exchange-alt';
            } else {
                cssClass += ' transcript-participant';
                icon = 'fas fa-user';
            }
            
            html += `
                <div class="${cssClass}">
                    <div class="transcript-speaker">
                        <i class="${icon} me-2"></i>${speaker}
                    </div>
                    <div class="transcript-content">${content}</div>
                    ${timestamp ? `<div class="transcript-meta">${timestamp}</div>` : ''}
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    initializeQA() {
        const conversation = document.getElementById('qa-conversation');
        conversation.innerHTML = `
            <div class="text-muted text-center">
                <i class="fas fa-robot me-2"></i>
                Ask any question about the focus group discussion!
            </div>
        `;
    }

    async askQuestion() {
        const questionInput = document.getElementById('qa-question');
        const question = questionInput.value.trim();
        
        if (!question) {
            this.showAlert('Please enter a question.', 'warning');
            return;
        }

        if (!this.currentSessionId) {
            this.showAlert('No active session found.', 'danger');
            return;
        }

        // Add question to conversation
        this.addQAMessage(question, 'question');
        questionInput.value = '';

        // Show typing indicator
        this.addTypingIndicator();

        try {
            const response = await fetch('/ask-question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    question: question
                })
            });

            const data = await response.json();

            // Remove typing indicator
            this.removeTypingIndicator();

            if (data.success && data.answer) {
                this.addQAMessage(data.answer.answer || data.answer, 'answer');
            } else {
                this.addQAMessage('Sorry, I couldn\'t process your question. Please try again.', 'answer');
            }
        } catch (error) {
            console.error('Error:', error);
            this.removeTypingIndicator();
            this.addQAMessage('Network error. Please try again.', 'answer');
        }
    }

    addQAMessage(message, type) {
        const conversation = document.getElementById('qa-conversation');
        
        // Clear welcome message if present
        if (conversation.querySelector('.text-muted')) {
            conversation.innerHTML = '';
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `qa-message qa-${type}`;
        
        const icon = type === 'question' ? 'fas fa-user' : 'fas fa-robot';
        const label = type === 'question' ? 'You' : 'AI Assistant';
        
        // Format message content for better display
        let formattedMessage = message;
        if (type === 'answer') {
            // Convert markdown-style formatting to HTML
            formattedMessage = message
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
                .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
                .replace(/\n\n/g, '</p><p>') // Paragraphs
                .replace(/\n/g, '<br>') // Line breaks
                .replace(/^(.+)$/g, '<p>$1</p>'); // Wrap in paragraph
            
            // Fix paragraph wrapping
            if (!formattedMessage.startsWith('<p>')) {
                formattedMessage = '<p>' + formattedMessage + '</p>';
            }
            
            // Clean up empty paragraphs
            formattedMessage = formattedMessage
                .replace(/<p><\/p>/g, '')
                .replace(/<p><br><\/p>/g, '<br>');
        }
        
        messageDiv.innerHTML = `
            <div class="mb-2">
                <strong><i class="${icon} me-2"></i>${label}:</strong>
            </div>
            <div class="message-content">${formattedMessage}</div>
        `;
        
        conversation.appendChild(messageDiv);
        conversation.scrollTop = conversation.scrollHeight;
    }

    addTypingIndicator() {
        const conversation = document.getElementById('qa-conversation');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'qa-message qa-answer';
        typingDiv.innerHTML = `
            <div class="mb-2">
                <strong><i class="fas fa-robot me-2"></i>AI Assistant:</strong>
            </div>
            <div>
                <i class="fas fa-circle-notch fa-spin me-2"></i>Thinking...
            </div>
        `;
        
        conversation.appendChild(typingDiv);
        conversation.scrollTop = conversation.scrollHeight;
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 10000; max-width: 400px;';
        
        const icons = {
            success: 'fas fa-check-circle',
            danger: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        alertDiv.innerHTML = `
            <i class="${icons[type] || icons.info} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
let focusGroupApp;
document.addEventListener('DOMContentLoaded', () => {
    focusGroupApp = new FocusGroupApp();
});

// Handle page visibility for polling
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, could pause polling
    } else {
        // Page is visible, resume polling if needed
    }
});