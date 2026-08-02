// ── Check if user is logged in ──────────────────────────────────────
function isLoggedIn() {
  const token = localStorage.getItem('jwt_token') || sessionStorage.getItem('jwt_token');
  if (!token) return false;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000;
    if (Date.now() >= exp) {
      localStorage.removeItem('jwt_token');
      sessionStorage.removeItem('jwt_token');
      localStorage.removeItem('username');
      return false;
    }
    return true;
  } catch (e) {
    return false;
  }
}

// ── Update navbar based on login status ─────────────────────────────
function updateNavbar() {
  const navButtons = document.getElementById('navButtons');
  const heroCta = document.getElementById('heroCtaBtn');
  
  // Book Now button - visible to everyone
  const bookBtn = `<button class="booking-btn" onclick="window.location.href='/booking'">📅 Book Now</button>`;
  
  if (isLoggedIn()) {
    // Show Book Now + Dashboard button
    navButtons.innerHTML = `
      ${bookBtn}
      <button class="dashboard-btn" onclick="window.location.href='/dashboard'">
         Open Dashboard
      </button>
    `;
    
    if (heroCta) {
      heroCta.innerHTML = 'Go to Dashboard →';
      heroCta.onclick = () => window.location.href = '/dashboard';
    }
  } else {
    // Show Book Now + Login button - NO REGISTER BUTTON
    navButtons.innerHTML = `
      ${bookBtn}
      <button class="login-btn" onclick="window.location.href='/login'">Login</button>
    `;
    
    if (heroCta) {
      heroCta.innerHTML = 'Book Now';
      heroCta.onclick = () => window.location.href = '/booking';
    }
  }
}

// ── Handle hero CTA button click ─────────────────────────────────────
function handleHeroCta() {
  if (isLoggedIn()) {
    window.location.href = '/dashboard';
  } else {
    window.location.href = '/booking';
  }
}

// ── Smooth scroll animation for navigation links ────────────────────
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

// ── Scroll animation - reveal elements when they come into view ──────
const observerOptions = {
  threshold: 0.2,
  rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

// Observe feature cards
const cards = document.querySelectorAll('.card');
cards.forEach(card => observer.observe(card));

// Observe about section
const aboutSection = document.querySelector('.about-content');
if (aboutSection) observer.observe(aboutSection);

// Observe stat items
const statItems = document.querySelectorAll('.stat-item');
statItems.forEach(item => observer.observe(item));

// ── Navbar shrink on scroll ──────────────────────────────────────────
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 50) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
});

// ── Scroll progress bar ──────────────────────────────────────────────
const scrollProgress = document.getElementById('scrollProgress');
window.addEventListener('scroll', () => {
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
  const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
  const scrollPercentage = (scrollTop / scrollHeight) * 100;
  scrollProgress.style.width = scrollPercentage + '%';
});

// ── Counter animation for stats ──────────────────────────────────────
function animateCounter(element, target) {
  let current = 0;
  const increment = target / 50;
  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      element.textContent = target.toLocaleString() + '+';
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current).toLocaleString() + '+';
    }
  }, 30);
}

// Trigger counter when stats become visible
const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const statNumbers = entry.target.querySelectorAll('.stat-number');
      statNumbers.forEach(stat => {
        const targetValue = parseInt(stat.textContent);
        if (!isNaN(targetValue) && stat.getAttribute('data-animated') !== 'true') {
          stat.setAttribute('data-animated', 'true');
          animateCounter(stat, targetValue);
        }
      });
      statsObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

const statsSection = document.querySelector('.stats');
if (statsSection) statsObserver.observe(statsSection);

// ── Parallax effect for hero section ──────────────────────────────────
window.addEventListener('scroll', () => {
  const scrolled = window.pageYOffset;
  const hero = document.querySelector('.hero');
  if (hero) {
    hero.style.backgroundPositionY = scrolled * 0.5 + 'px';
  }
});

// ── Add floating animation delay to cards ────────────────────────────
cards.forEach((card, index) => {
  card.style.transitionDelay = `${index * 0.1}s`;
});

// ── Preload animation for elements already visible on page load ──────
setTimeout(() => {
  cards.forEach(card => {
    const rect = card.getBoundingClientRect();
    if (rect.top < window.innerHeight - 100) {
      card.classList.add('visible');
    }
  });
  if (aboutSection && aboutSection.getBoundingClientRect().top < window.innerHeight - 100) {
    aboutSection.classList.add('visible');
  }
  statItems.forEach(item => {
    if (item.getBoundingClientRect().top < window.innerHeight - 100) {
      item.classList.add('visible');
    }
  });
}, 100);

// ── Initialize navbar on page load ───────────────────────────────────
updateNavbar();

// ── Also check when returning to page ────────────────────────────────
window.addEventListener('pageshow', () => {
  updateNavbar();
});