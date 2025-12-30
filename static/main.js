document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const processBtn = document.getElementById('process-btn');
    const sensitivitySlider = document.getElementById('sensitivity');

    // Status Elements
    const statusArea = document.getElementById('status-area');
    const loader = document.getElementById('loader');
    const resultSuccess = document.getElementById('result-success');
    const resultError = document.getElementById('result-error');
    const downloadLink = document.getElementById('download-link');
    const errorMessage = document.getElementById('error-message');
    const resetBtns = document.querySelectorAll('.reset-btn');

    let selectedFile = null;

    // --- Drag & Drop Interface ---
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.type !== 'application/pdf') {
                alert('Please upload a PDF file.');
                return;
            }
            selectedFile = file;
            updateUIForFile(file);
        }
    }

    function updateUIForFile(file) {
        const icon = dropZone.querySelector('.icon-container i');
        const h3 = dropZone.querySelector('h3');
        const p = dropZone.querySelector('p');

        icon.className = 'ph-duotone ph-file-pdf'; // Change icon
        h3.textContent = file.name;
        p.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;

        processBtn.disabled = false;
    }

    // --- Processing ---
    processBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // UI Updates
        processBtn.disabled = true;
        dropZone.style.pointerEvents = 'none';
        statusArea.classList.remove('hidden');
        loader.classList.remove('hidden');
        resultSuccess.classList.add('hidden');
        resultError.classList.add('hidden');

        // Prepare Data
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('sensitivity', sensitivitySlider.value);

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            loader.classList.add('hidden');

            if (response.ok && data.status === 'success') {
                showSuccess(data);
            } else {
                showError(data.error || data.message || 'Unknown error occurred');
            }

        } catch (error) {
            console.error(error);
            loader.classList.add('hidden');
            showError('Failed to connect to the server.');
        }
    });

    function showSuccess(data) {
        resultSuccess.classList.remove('hidden');
        downloadLink.href = data.download_url;
        downloadLink.download = ''; // Let browser handle name
    }

    function showError(msg) {
        resultError.classList.remove('hidden');
        errorMessage.textContent = msg;
    }

    // --- Reset ---
    resetBtns.forEach(btn => btn.addEventListener('click', resetUI));

    function resetUI() {
        selectedFile = null;
        fileInput.value = '';

        // Reset Drop Zone
        const icon = dropZone.querySelector('.icon-container i');
        const h3 = dropZone.querySelector('h3');
        const p = dropZone.querySelector('p');

        icon.className = 'ph-duotone ph-cloud-arrow-up';
        h3.textContent = 'Upload your PDF';
        p.innerHTML = 'Drag & drop or <span class="browse-btn">browse files</span>';
        dropZone.style.pointerEvents = 'all';

        processBtn.disabled = true;
        statusArea.classList.add('hidden');
    }
});
