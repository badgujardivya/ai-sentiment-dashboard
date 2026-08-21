                nav.classList.remove('active'));
                item.classList.add('active');
            }
        });
    });
}

function initAnimations() {
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all animated elements
    document.querySelectorAll('.glass, .kpi-card, .feature-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
}

// Example dataset for testing (create this CSV file)
// You can download sample data from Kaggle or create your own
function createSampleData() {
    const sampleData = [
        { review: "The product quality is amazing and delivery was fast!", sentiment: "positive" },
        { review: "Terrible support, waited 3 days for response", sentiment: "negative" },
        { review: "Average product, nothing special", sentiment: "neutral" },
        // Add more rows...
    ];
    
    // This is just for demo - replace with real CSV upload
}

// Auto-initialize if on dashboard page
if (document.querySelector('.dashboard-container')) {
    currentAnalysisId = window.analysisData?.analysis_id || 
                       new URLSearchParams(window.location.search).get('analysis_id');
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Voice input (Bonus feature)
if ('webkitSpeechRecognition' in window) {
    const predictText = document.getElementById('predictText');
    if (predictText) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        // Add voice button if predict section exists
        const voiceBtn = document.createElement('button');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceBtn.className = 'btn btn-secondary voice-btn';
        voiceBtn.title = 'Voice Input';
        
        predictText.parentNode.insertBefore(voiceBtn, predictText.nextSibling);
        
        voiceBtn.addEventListener('click', () => {
            recognition.start();
            voiceBtn.classList.add('recording');
        });
        
        recognition.onresult = (event) => {
            predictText.value = event.results[0][0].transcript;
            voiceBtn.classList.remove('recording');
        };
        
        recognition.onerror = () => {
            voiceBtn.classList.remove('recording');
        };
    }
}

// Export charts (Bonus feature)
function exportChart(chartId, filename) {
    Plotly.downloadImage({
        format: 'png',
        filename: filename,
        width: 800,
        height: 600
    }, document.getElementById(chartId));
}

// Add export buttons to charts
document.addEventListener('DOMContentLoaded', () => {
    const charts = document.querySelectorAll('.chart-card');
    charts.forEach((chart, index) => {
        const exportBtn = document.createElement('button');
        exportBtn.innerHTML = '<i class="fas fa-download"></i>';
        exportBtn.className = 'btn btn-secondary btn-sm export-btn';
        exportBtn.title = 'Export Chart';
        exportBtn.onclick = () => exportChart(chart.querySelector('[id]').id, `chart-${index + 1}`);
        chart.appendChild(exportBtn);
    });
});

// Loading animation for dashboard charts
function initChartLoading() {
    const chartContainers = document.querySelectorAll('.chart-card div[id]');
    chartContainers.forEach(container => {
        container.innerHTML = '<div class="chart-loading"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
    });
}