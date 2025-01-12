// Store captured preview data
const capturedPreviews = new Map();

// Monitor network requests to catch preview URLs
function setupPreviewMonitor() {
    // Monitor XHR requests
    const origXHR = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(...args) {
        const url = args[1];
        if (url && typeof url === 'string' &&
            url.includes('previews.dropbox.com/p/pdf_img/')) {
            console.log('Found preview URL via XHR:', url);
            if (lastClickedId) {
                updateCapturedData(lastClickedId, url);
            }
        }
        return origXHR.apply(this, args);
    };

    // Monitor fetch requests
    const origFetch = window.fetch;
    window.fetch = async (...args) => {
        const url = typeof args[0] === 'string' ? args[0] : args[0]?.url;
        if (url && typeof url === 'string' &&
            url.includes('previews.dropbox.com/p/pdf_img/')) {
            console.log('Found preview URL via fetch:', url);
            if (lastClickedId) {
                updateCapturedData(lastClickedId, url);
            }
        }
        return origFetch.apply(this, args);
    };

    // Add image request monitoring for specific Dropbox preview URLs
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeName === 'IMG' &&
                    node.src &&
                    node.src.includes('previews.dropbox.com/p/pdf_img/')) {
                    console.log('Found preview URL via img:', node.src);
                    if (lastClickedId) {
                        updateCapturedData(lastClickedId, node.src);
                    }
                }
            });
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    console.log('Network monitoring enabled for XHR, fetch, and image elements');
}

let lastClickedId = null;

// Function to load all versions
async function loadAllVersions() {
    console.log('Starting to load all versions...');

    while (true) {
        const loadMoreButton = document.querySelector('button.load-more-revisions');

        if (!loadMoreButton || !loadMoreButton.offsetParent) {
            console.log('No more versions to load');
            break;
        }

        const currentVersionCount = document.querySelectorAll('li[data-identity]').length;
        console.log(`Currently loaded versions: ${currentVersionCount}`);

        loadMoreButton.click();
        console.log('Clicked load more button, waiting for versions to load...');

        // Wait for new versions to load
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Verify that new versions were actually loaded
        const newVersionCount = document.querySelectorAll('li[data-identity]').length;
        if (newVersionCount === currentVersionCount) {
            console.log('No new versions loaded, stopping');
            break;
        }
    }

    const totalVersions = document.querySelectorAll('li[data-identity]').length;
    console.log(`Finished loading versions. Total versions loaded: ${totalVersions}`);
}

function combineToISO(datestr, timestamp){
    // datestr: ['Today', 'Yesterday', 'January 9, 2025', 'January 8, 2025']
    // timestamp: '2:52 PM'
    let baseDate = new Date();
    if (datestr === 'Today'){
        datestr = baseDate.toDateString();
    }
    else if (datestr === 'Yesterday'){
        baseDate.setDate(baseDate.getDate() - 1);
        datestr = baseDate.toDateString();
    }
    return new Date(`${datestr} ${timestamp}`).toISOString()
}

function getTimestamp(row) {
    let text = x => x ? x.textContent.trim() : '';
    const dateEl = row.parentNode.parentNode.querySelector('span.revision-date');
    const timeEl = row.querySelector('.file-revisions__text--time, [data-testid="timestamp"]');

    return combineToISO(text(dateEl), text(timeEl));
}

function updateCapturedData(versionId, url) {
    const row = document.querySelector(`li[data-identity="${versionId}"]`);
    if (row) {
        const ts = getTimestamp(row);
        const existingData = capturedPreviews.get(versionId);

        // Only update if we don't already have this URL
        if (!existingData || existingData.previewUrl !== url) {
            console.log(`Updating captured data for version ${versionId}: timestamp: ${ts}, URL: ${url}`);
            capturedPreviews.set(versionId, {
                timestamp: ts,
                previewUrl: url
            });
            updateProgress();
        }
    }
}

// Function to close the preview modal
async function closePreview() {
    await new Promise(resolve => setTimeout(resolve, 1000));
    const closeButton = document.querySelector('[data-testid="preview-close"], .preview-close, .modal-close');
    if (closeButton) {
        closeButton.click();
        return true;
    }
    return false;
}

// Click each version row to trigger preview loading
async function captureAllPreviews() {
    // First, load all versions
    await loadAllVersions();

    const rows = Array.from(document.querySelectorAll('li[data-identity]'));
    console.log(`Starting to capture ${rows.length} previews...`);

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const versionId = row.getAttribute('data-identity');
        console.log(`Processing version ${i + 1}/${rows.length}, ID: ${versionId}`);

        if (!capturedPreviews.has(versionId)) {
            lastClickedId = versionId;

            // Scroll the row into view
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            await new Promise(resolve => setTimeout(resolve, 500));

            // Click to open preview
            row.click();
            console.log('Clicked version row, waiting for preview...');

            // Wait for preview to load
            await new Promise(resolve => setTimeout(resolve, 3000));

            // Close preview
            const closed = await closePreview();
            if (!closed) {
                console.log('Warning: Failed to close preview for version:', versionId);
            }

            // Wait before next iteration
            await new Promise(resolve => setTimeout(resolve, 2000));

            console.log('Completed processing version:', versionId);
            console.log('Current captured URLs:', capturedPreviews.size);
        }
    }

    // Final update
    save();
}

function save(){
    const jsonData = Array.from(capturedPreviews.entries())
        .map(([id, data]) => ({
            id: id,
            timestamp: data.timestamp,
            url: data.previewUrl
        }));

    const jsonString = JSON.stringify(jsonData, null, 2);

    console.log('\nAll preview data captured! Copied to clipboard.');
    console.log('\nPreview data:');
    console.log(jsonString);

    // Create temporary textarea to copy to clipboard
    const textarea = document.createElement('textarea');
    textarea.value = jsonString;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
}

// Show progress and copy results
function updateProgress() {
    const totalVersions = document.querySelectorAll('li[data-identity]').length;
    const currentCount = capturedPreviews.size;
    console.log(`Progress: ${currentCount}/${totalVersions} previews captured`);
}

// Initialize and run
const start = new Date();
setupPreviewMonitor();
await captureAllPreviews();
const totalVersions = document.querySelectorAll('li[data-identity]').length;
const currentCount = capturedPreviews.size;
console.log(`Progress: ${currentCount}/${totalVersions} previews captured`);
const end = new Date();
console.log(`Elapsed time: ${new Date(end - start).toISOString().substr(11, 8)}`);
