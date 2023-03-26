const previousPage = {
  btn: document.getElementById("previousPageBtn"),
  link: document.getElementById("previousPageLink"),
};
const nextPage = {
  btn: document.getElementById("nextPageBtn"),
  link: document.getElementById("nextPageLink"),
};
const currentPage = Number(previousPage.link.getAttribute("href").split("=")[1]) + 1;

// Subtracted by two because the "previous" and "next" buttons don't count
const pageCount = document.querySelectorAll(".page-item").length - 2;

function onReady() {
  if (currentPage - 1 <= 0) {
    previousPage.btn.classList.add("disabled");
    previousPage.link.setAttribute("href", "");
  }
  if (currentPage + 1 > pageCount) {
    nextPage.btn.classList.add("disabled");
    nextPage.link.setAttribute("href", "");
  }
}

onReady();
