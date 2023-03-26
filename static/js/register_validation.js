const formID = {
  username: "username",
  password: "password",
  confirmPassword: "confirmPassword",
  submitBtn: "submitBtn",
};
const invalidID = {
  password: "invalidPassword",
  confirmPassword: "invalidConfirmPassword",
  username: "invalidUsername",
};

const usernameLimit = 30;
const passwordLimit = 50;

function showApology(tagID, message) {
  const tag = document.getElementById(tagID);
  tag.style.display = "inline";
  tag.innerHTML = message;
}

function resetFormValidation() {
  for (let key of Object.keys(invalidID)) {
    document.getElementById(invalidID[key]).style.display = "none";
  }
}

function validateForm() {
  resetFormValidation();

  const username = document.getElementById(formID.username).value;
  const password = document.getElementById(formID.password).value;
  const confirmPassword = document.getElementById(formID.confirmPassword).value;
  let formValidated = true;

  if (username.length > usernameLimit) {
    showApology(
      invalidID.username,
      `Username must not be greater than ${usernameLimit} characters!`
    );
    formValidated = false;
  }
  if (password.length > passwordLimit) {
    showApology(
      invalidID.password,
      `Password must not be greater than ${passwordLimit} characters!`
    );
    formValidated = false;
  } else if (password !== confirmPassword) {
    const passwordIDs = [invalidID.password, invalidID.confirmPassword];
    for (let id of passwordIDs) {
      showApology(
        id,
        "Password field and confirm password field do not match!"
      );
    }
    formValidated = false;
  }

  if (formValidated) {
    submitForm();
  }
}

function submitForm() {
  const submitBtn = document.getElementById(formID.submitBtn);
  submitBtn.setAttribute("type", "submit");
}

function onReady() {
  const submitBtn = document.getElementById(formID.submitBtn);
  submitBtn.addEventListener("click", () => {
    validateForm();
  });

  const usernameTakenTag = document.getElementById("usernameTakenFeedback");
  if (usernameTakenTag) {
    showApology(
      usernameTakenTag.getAttribute("id"),
      "Username is already taken!"
    );
    usernameTakenTag.setAttribute("id", invalidID.username);
  }
}

onReady();
