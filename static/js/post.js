const reportTitleContentElement = document.getElementById("reportContent");

const commentReports = document.getElementsByClassName("comment-report");
const commentIdInputField = document.getElementById("commentIdField");

const reportForm = document.getElementById("reportForm");
const reportPostButton = document.getElementById("reportPostBtn");
const reportPostLink = reportForm.getAttribute("action");

const formInfo = {
  authorUsername: reportPostLink.split("/")[2],
  isCommentReport: false,
};

function updateFormAction() {
  if (formInfo.isCommentReport) {
    const commentId = commentIdInputField.getAttribute("value");
    reportForm.setAttribute(
      "action",
      `/users/${formInfo.authorUsername}/comments/${commentId}/report`
    );
  } else {
    reportForm.setAttribute("action", reportPostLink);
  }
}

function onPostReport() {
  reportTitleContentElement.innerHTML = "post";
  formInfo.isCommentReport = false;
  updateFormAction();
}

function onCommentReport(id) {
  reportTitleContentElement.innerHTML = "comment";
  commentIdInputField.setAttribute("value", id);
  formInfo.isCommentReport = true;
  updateFormAction();
}

function onReady() {
  for (let i = 0; i < commentReports.length; i++) {
    commentReports[i].setAttribute(
      "onclick",
      `onCommentReport(${commentReports[i].id})`
    );
  }
  reportPostButton.addEventListener("click", onPostReport);
}

onReady();
