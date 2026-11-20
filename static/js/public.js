// static/js/public.js

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Sticky Navbar Scroll Effect (Smooth Transition)
    const navbar = document.getElementById('navbar');
    if (navbar) {
        const handleScroll = () => {
            if (window.scrollY > 20) {
                navbar.classList.add('shadow-md', 'bg-white/95', 'backdrop-blur-lg', 'border-[#E5E7EB]');
                navbar.classList.remove('bg-white/80', 'border-transparent');
            } else {
                navbar.classList.remove('shadow-md', 'bg-white/95', 'backdrop-blur-lg', 'border-[#E5E7EB]');
                navbar.classList.add('bg-white/80', 'border-transparent');
            }
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll(); // Run once on load
    }

    // 2. Mobile Menu Toggle with Smooth Icon Transition
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileBtn && mobileMenu) {
        mobileBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
            const icon = mobileBtn.querySelector('i');
            if (mobileMenu.classList.contains('hidden')) {
                icon.setAttribute('data-lucide', 'menu');
            } else {
                icon.setAttribute('data-lucide', 'x');
            }
            lucide.createIcons();
        });
    }

    // 3. Advanced Scroll Reveal Animations (IntersectionObserver)
    const revealElements = document.querySelectorAll('.reveal');
    
    if (revealElements.length > 0) {
        const revealOptions = {
            root: null,
            threshold: 0.15, // Trigger when 15% of the element is visible
            rootMargin: "0px 0px -50px 0px" 
        };

        const revealOnScroll = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    observer.unobserve(entry.target); // Stop observing once revealed
                }
            });
        }, revealOptions);

        revealElements.forEach(el => revealOnScroll.observe(el));
    }

    // 4. Smooth Anchor Scrolling for Navigation Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                
                // Close mobile menu if open
                if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                    mobileBtn.click();
                }

                const headerOffset = 80; // Adjust for sticky navbar height
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // 5. Premium Spotlight Effect for Feature Cards (Mouse Tracking)
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Set CSS custom properties to be used in the template's gradient
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });

    // 6. Number Count-Up Animation (For trust indicators, if added later)
    const counters = document.querySelectorAll('.counter-value');
    const speed = 200; // The lower the slower

    if (counters.length > 0) {
        const runCounter = (counter) => {
            const updateCount = () => {
                const target = +counter.getAttribute('data-target');
                const count = +counter.innerText;
                const inc = target / speed;

                if (count < target) {
                    counter.innerText = Math.ceil(count + inc);
                    setTimeout(updateCount, 20);
                } else {
                    counter.innerText = target;
                }
            };
            updateCount();
        };

        // Trigger count-up when visible
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    runCounter(entry.target);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => counterObserver.observe(counter));
    }
});