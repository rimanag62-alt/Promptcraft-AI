// PromptCraft AI - Interactive Studio Workspace Controller
document.addEventListener('DOMContentLoaded', () => {
    const workspaceElement = document.getElementById('workspace-app');
    if (!workspaceElement) return;

    const projectId = workspaceElement.dataset.projectId;
    const previewUrl = workspaceElement.dataset.previewUrl;

    const codeContentElem = document.getElementById('code-content');
    const currentFileNameElem = document.getElementById('current-file-name');
    const currentFileSizeElem = document.getElementById('current-file-size');
    const copyCodeBtn = document.getElementById('btn-copy-code');
    const previewIframe = document.getElementById('preview-iframe');
    const reloadPreviewBtn = document.getElementById('btn-reload-preview');
    const previewContainer = document.getElementById('preview-container');
    const historyBtn = document.getElementById('btn-toggle-history');
    const historyDrawer = document.getElementById('history-drawer');
    const iterationForm = document.getElementById('iteration-form');
    const iterationSubmitBtn = document.getElementById('btn-submit-iteration');
    const iterationInput = document.getElementById('iteration-input');

    // ------------------ File Tree & Code Viewer ------------------
    function selectFile(relPath, nodeElem) {
        document.querySelectorAll('.tree-node').forEach(n => n.classList.remove('active'));
        if (nodeElem) {
            nodeElem.classList.add('active');
        }

        currentFileNameElem.textContent = relPath;
        codeContentElem.textContent = 'Loading file content...';

        fetch(`/projects/${projectId}/files/${encodeURIComponent(relPath)}`)
            .then(res => {
                if (!res.ok) throw new Error('Could not load file');
                return res.json();
            })
            .then(data => {
                codeContentElem.textContent = data.content;
                currentFileSizeElem.textContent = formatBytes(data.file_size || data.content.length);
            })
            .catch(err => {
                codeContentElem.textContent = `Error reading file: ${err.message}`;
            });
    }

    document.querySelectorAll('.tree-node.file').forEach(node => {
        node.addEventListener('click', () => {
            const relPath = node.dataset.path;
            selectFile(relPath, node);
        });
    });

    function formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    // ------------------ Copy Code ------------------
    if (copyCodeBtn) {
        copyCodeBtn.addEventListener('click', () => {
            const code = codeContentElem.textContent;
            navigator.clipboard.writeText(code).then(() => {
                const originalHtml = copyCodeBtn.innerHTML;
                copyCodeBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                setTimeout(() => {
                    copyCodeBtn.innerHTML = originalHtml;
                }, 2000);
            });
        });
    }

    // ------------------ Device Viewport Switching ------------------
    document.querySelectorAll('.device-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.device-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const device = btn.dataset.device;
            previewContainer.classList.remove('desktop', 'tablet', 'mobile');
            previewContainer.classList.add(device);
        });
    });

    // ------------------ Refresh Preview ------------------
    if (reloadPreviewBtn) {
        reloadPreviewBtn.addEventListener('click', () => {
            if (previewIframe) {
                // Add timestamp query parameter to bypass browser iframe caching
                const base = previewUrl.split('?')[0];
                previewIframe.src = `${base}?t=${Date.now()}`;
            }
        });
    }

    // ------------------ Iteration History Drawer ------------------
    if (historyBtn && historyDrawer) {
        historyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            historyDrawer.classList.toggle('active');
        });

        document.addEventListener('click', (e) => {
            if (!historyDrawer.contains(e.target) && e.target !== historyBtn) {
                historyDrawer.classList.remove('active');
            }
        });
    }

    // ------------------ Iteration Prompt Submission ------------------
    if (iterationForm) {
        iterationForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const promptText = iterationInput.value.trim();
            if (!promptText) return;

            iterationSubmitBtn.disabled = true;
            iterationSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Updating...';
            iterationInput.disabled = true;

            const formData = new FormData();
            formData.append('prompt', promptText);

            fetch(`/projects/${projectId}/iterate/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Accept': 'application/json'
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(`Iteration failed: ${data.error || 'Unknown error'}`);
                    iterationSubmitBtn.disabled = false;
                    iterationSubmitBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Update App';
                    iterationInput.disabled = false;
                }
            })
            .catch(err => {
                alert(`Error: ${err.message}`);
                iterationSubmitBtn.disabled = false;
                iterationSubmitBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Update App';
                iterationInput.disabled = false;
            });
        });
    }
});
