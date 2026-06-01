document.addEventListener('DOMContentLoaded', function () {
    // === SIDEBAR TOGGLE LOGIC ===
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');

    if (toggleBtn && sidebar && overlay) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        });

        overlay.addEventListener('click', () => {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    // === PARTICLES.JS INITIALIZATION ===
    if (document.getElementById('particles-js')) {
        const blueShades = ['#112240', '#1a3a63', '#2a4a7f', '#4a8fe7', '#64b5f6'];

        // Check if particlesJS is loaded
        if (typeof particlesJS !== 'undefined') {
            particlesJS('particles-js', {
                particles: {
                    number: {
                        value: 120,
                        density: { enable: true, value_area: 1000 }
                    },
                    color: { value: blueShades },
                    shape: { type: 'circle' },
                    opacity: {
                        value: 0.8,
                        random: true,
                        anim: { enable: true, speed: 1, opacity_min: 0.3, sync: false }
                    },
                    size: {
                        value: 4,
                        random: true,
                        anim: { enable: true, speed: 3, size_min: 1, sync: false }
                    },
                    line_linked: {
                        enable: true,
                        distance: 180,
                        color: '#4a8fe7',
                        opacity: 0.5,
                        width: 1.2
                    },
                    move: {
                        enable: true,
                        speed: 2,
                        direction: 'none',
                        random: true,
                        straight: false,
                        out_mode: 'bounce',
                        bounce: false,
                        attract: { enable: true, rotateX: 600, rotateY: 1200 }
                    }
                },
                interactivity: {
                    detect_on: 'window',
                    events: {
                        onhover: { enable: true, mode: 'grab' },
                        onclick: { enable: true, mode: 'push' },
                        resize: true
                    },
                    modes: {
                        grab: { distance: 180, line_linked: { opacity: 0.8 } },
                        push: { particles_nb: 6 }
                    }
                },
                retina_detect: true
            });

            // Adjust canvas on resize
            window.addEventListener('resize', function () {
                if (window.pJSDom && window.pJSDom.length > 0) {
                    window.pJSDom[0].pJS.fn.canvasPaint();
                }
            });
        }
    }
});
