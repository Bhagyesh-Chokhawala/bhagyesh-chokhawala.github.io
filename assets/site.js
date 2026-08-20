(() => {
  "use strict";

  const navigationMarkup = `
    <a href="/index.html" data-nav-page="home">Home</a>
    <a href="/publications.html" data-nav-page="publications">Publications</a>
    <a href="/publications.html#upcoming" data-nav-page="upcoming">Upcoming Publications</a>
    <a href="/blogs.html" data-nav-page="blogs">Blog Stories</a>
    <div class="site-nav-dropdown">
      <button class="site-nav-dropdown-trigger" type="button" aria-haspopup="true">Demo Portals</button>
      <div class="site-nav-dropdown-menu">
        <a href="/api-policy-portal/">API Policy Portal</a>
        <a href="/enterprise-ai-standards-portal/">Enterprise AI Standards Portal</a>
      </div>
    </div>
    <a href="/contact.html" data-nav-page="contact">Contact</a>`;

  const currentPage = (() => {
    const path = window.location.pathname.toLowerCase();
    if (path.endsWith("/blogs.html")) return "blogs";
    if (path.endsWith("/contact.html")) return "contact";
    if (path.endsWith("/upcomingpublications.html") || (path.endsWith("/publications.html") && window.location.hash === "#upcoming")) return "upcoming";
    if (path.includes("/publications/") || path.endsWith("/publications.html")) return "publications";
    if (path === "/" || path.endsWith("/index.html")) return "home";
    return "";
  })();

  document.querySelectorAll("[data-site-navigation]").forEach((navigation) => {
    navigation.innerHTML = navigationMarkup;
    const activeLink = navigation.querySelector(`[data-nav-page="${currentPage}"]`);
    if (activeLink) activeLink.setAttribute("aria-current", "page");
  });

  document.querySelectorAll(".portal-showcases").forEach((carousel) => {
    const scroller = carousel.querySelector(".portal-showcase-scroller");
    const previous = carousel.querySelector(".portal-carousel-previous");
    const next = carousel.querySelector(".portal-carousel-next");
    if (!scroller || !previous || !next) return;

    const updateControls = () => {
      previous.disabled = scroller.scrollLeft <= 2;
      next.disabled = scroller.scrollLeft >= scroller.scrollWidth - scroller.clientWidth - 2;
    };
    const move = (direction) => scroller.scrollBy({
      left: direction * scroller.clientWidth,
      behavior: "smooth"
    });

    previous.addEventListener("click", () => move(-1));
    next.addEventListener("click", () => move(1));
    scroller.addEventListener("scroll", updateControls, { passive: true });
    window.addEventListener("resize", updateControls);
    updateControls();
  });

  const year = String(new Date().getFullYear());
  document.querySelectorAll("[data-current-year]").forEach((element) => {
    element.textContent = year;
  });
})();
