document.addEventListener("DOMContentLoaded", () => {
  const current = document.querySelector(".nav-item.is-current > a");
  if (current) {
    current.scrollIntoView({ block: "nearest" });
  }
});
