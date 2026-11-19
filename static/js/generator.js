// PromptCraft AI - Generator Controller
document.addEventListener('DOMContentLoaded', () => {
    const generatorForm = document.getElementById('generator-form');
    const promptInput = document.getElementById('id_prompt');
    const titleInput = document.getElementById('id_title');
    const categorySelect = document.getElementById('id_category');
    const submitBtn = document.getElementById('btn-generate-submit');
    const loadingOverlay = document.getElementById('generation-loading-overlay');
    const statusStepElem = document.getElementById('status-step-text');

    // ------------------ Template Card Quick-Fill ------------------
    document.querySelectorAll('.template-card').forEach(card => {
        card.addEventListener('click', () => {
            const title = card.dataset.title;
            const category = card.dataset.category;
            const prompt = card.dataset.prompt;

            if (titleInput) titleInput.value = title;
            if (categorySelect) categorySelect.value = category;
            if (promptInput) {
                promptInput.value = prompt;
                promptInput.focus();
            }

            // Smooth scroll to form
            window.scrollTo({ top: generatorForm.offsetTop - 90, behavior: 'smooth' });
        });
    });

    // ------------------ Form Submission & Loading Overlay ------------------
    if (generatorForm) {
        generatorForm.addEventListener('submit', (e) => {
            const promptVal = promptInput.value.trim();
            if (!promptVal) return;

            // Show loading animation
            if (loadingOverlay) {
                loadingOverlay.classList.add('active');
                animateStatusSteps();
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating App...';
            }
        });
    }

    function animateStatusSteps() {
        const steps = [
            "Analyzing prompt requirements...",
            "Synthesizing HTML5 semantic layout...",
            "Crafting responsive CSS3 styling & theme variables...",
            "Writing Vanilla JavaScript & localStorage state management...",
            "Packaging workspace files and configuring live preview..."
        ];

        let index = 0;
        const interval = setInterval(() => {
            index++;
            if (index < steps.length && statusStepElem) {
                statusStepElem.textContent = steps[index];
            } else {
                clearInterval(interval);
            }
        }, 1800);
    }
});
