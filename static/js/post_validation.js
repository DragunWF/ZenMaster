const formID = {
  title: "title",
  content: "content",
};

const invalidTitle = document.getElementById("invalidTitle");
const invalidContent = document.getElementById("invalidContent");
const submitBtn = document.getElementById("submitBtn");
const resetBtn = document.getElementById("resetBtn");

const titleLimit = 50;
const contentLimit = 2000;

function showApology(id, message) {
  const tag = document.getElementById(id);
  tag.style.display = "inline";
  tag.innerHTML = message;
}

function resetFormValidation() {
  const invalidIDs = [
    invalidTitle.getAttribute("id"),
    invalidContent.getAttribute("id"),
  ];
  for (let id of invalidIDs) {
    document.getElementById(id).style.display = "none";
  }
}

function validateForm() {
  resetFormValidation();

  const title = document.getElementById("title").value;
  const content = document.getElementById("content").value;
  let formValidated = true;

  if (title.length > titleLimit) {
    showApology(
      invalidTitle.getAttribute("id"),
      `Title must not be greater than ${titleLimit} characters!`
    );
    formValidated = false;
  }
  if (content.length > contentLimit) {
    showApology(
      invalidContent.getAttribute("id"),
      `Content must not be greater than ${contentLimit} characters!`
    );
    formValidated = false;
  }

  if (formValidated) {
    submitForm();
  }
}

function submitForm() {
  submitBtn.setAttribute("type", "submit");
}

function onReady() {
  submitBtn.addEventListener("click", () => {
    validateForm();
  });
  resetBtn.addEventListener("click", () => {
    resetFormValidation();
  });
}

onReady();
