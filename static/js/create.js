const postTitle = document.getElementById("title");
const postContent = document.getElementById("content");
const resetButton = document.getElementById("resetBtn");

resetButton.addEventListener("click", () => {
  postTitle.value = "";
  postContent.value = "";
});
