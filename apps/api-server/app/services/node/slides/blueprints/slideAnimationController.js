/**
 * Slide Animation Controller
 * 
 * Progressive reveal system for educational slides.
 * Controls step-by-step content reveals with smooth animations.
 * Designed for button control (current) and future audio sync.
 */

class SlideAnimationController {
    constructor(config = {}) {
        this.currentStep = 0;
        this.totalSteps = 0;
        this.elements = [];
        this.onStepChange = config.onStepChange || null;

        // Button references
        this.prevBtn = null;
        this.nextBtn = null;
    }

    /**
     * Initialize the controller
     * - Find all elements with data-reveal-step
     * - Hide all content initially
     * - Set up button listeners
     */
    init() {
        // Find all animatable elements
        this.elements = Array.from(
            document.querySelectorAll('[data-reveal-step]')
        ).sort((a, b) => {
            return parseInt(a.dataset.revealStep) - parseInt(b.dataset.revealStep);
        });

        this.totalSteps = this.elements.length;

        // Hide all elements initially
        this.elements.forEach(el => {
            el.classList.add('reveal-hidden');
            el.classList.remove('reveal-visible');
        });

        // Set up navigation buttons
        this.setupButtons();

        // Start at step 0 (nothing visible)
        this.currentStep = 0;
        this.updateButtonStates();

        console.log(`SlideAnimationController initialized: ${this.totalSteps} steps`);
    }

    /**
     * Set up Previous/Next button event listeners
     */
    setupButtons() {
        this.prevBtn = document.getElementById('slidePrevBtn');
        this.nextBtn = document.getElementById('slideNextBtn');

        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.previous());
        }

        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.next());
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                e.preventDefault();
                this.next();
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault();
                this.previous();
            }
        });
    }

    /**
     * Reveal next element
     */
    next() {
        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            this.goToStep(this.currentStep);
        }
    }

    /**
     * Go back to previous step
     */
    previous() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.goToStep(this.currentStep);
        }
    }

    /**
     * Jump to specific step
     * @param {number} step - Target step (1-indexed, 0 = all hidden)
     */
    goToStep(step) {
        this.currentStep = Math.max(0, Math.min(step, this.totalSteps));

        // Update visibility for all elements
        this.elements.forEach((el, index) => {
            const elementStep = index + 1; // 1-indexed

            if (elementStep <= this.currentStep) {
                // Show this element
                el.classList.remove('reveal-hidden');
                el.classList.add('reveal-visible');
            } else {
                // Hide this element
                el.classList.remove('reveal-visible');
                el.classList.add('reveal-hidden');
            }
        });

        this.updateButtonStates();

        // Callback for external listeners (future audio sync)
        if (this.onStepChange) {
            this.onStepChange(this.currentStep, this.totalSteps);
        }
    }

    /**
     * Update button enabled/disabled states
     */
    updateButtonStates() {
        if (this.prevBtn) {
            this.prevBtn.disabled = this.currentStep === 0;
        }

        if (this.nextBtn) {
            this.nextBtn.disabled = this.currentStep === this.totalSteps;
        }

        // Update step indicator if it exists
        const indicator = document.getElementById('slideStepIndicator');
        if (indicator) {
            indicator.textContent = `${this.currentStep} / ${this.totalSteps}`;
        }
    }

    /**
     * Get current step number
     */
    getCurrentStep() {
        return this.currentStep;
    }

    /**
     * Get total number of steps
     */
    getTotalSteps() {
        return this.totalSteps;
    }

    /**
     * Reset to initial state (all hidden)
     */
    reset() {
        this.goToStep(0);
    }
}

// Auto-initialize if slideAutoInit is true
document.addEventListener('DOMContentLoaded', () => {
    if (window.slideAutoInit !== false) {
        window.slideController = new SlideAnimationController();
        window.slideController.init();
    }
});
