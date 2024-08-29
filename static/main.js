const primaryHeader = document.querySelector(".primary-header");
const navToggle = document.querySelector(".mobile-nav-toggle");
const primaryNav = document.querySelector(".primary-navigation");

navToggle.addEventListener("click", () => {
  primaryNav.hasAttribute("data-visible")
    ? navToggle.setAttribute("aria-expanded", false)
    : navToggle.setAttribute("aria-expanded", true);
  primaryNav.toggleAttribute("data-visible");
  primaryHeader.toggleAttribute("data-overlay");
});

///funzione searchbar

document.getElementById("search-button").addEventListener("click", function () {
  const query = document.getElementById("search-input").value;
  const category = document.getElementById("filter-category").value;

  fetch(
    `/search?query=${encodeURIComponent(query)}&category=${encodeURIComponent(
      category
    )}`
  )
    .then((response) => response.json())
    .then((data) => {
      const resultsContainer = document.getElementById("results-container");
      resultsContainer.innerHTML = "";

      if (data.length === 0) {
        resultsContainer.innerHTML = "<p>Nessun risultato trovato</p>";
      } else {
        data.forEach((item) => {
          const itemElement = document.createElement("div");
          itemElement.textContent = `${item.name} (${item.type})`;
          resultsContainer.appendChild(itemElement);
        });
      }
    });
});
