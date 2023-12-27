const draggables = document.querySelectorAll(".item");
const droppables = document.querySelectorAll(".swim-lane");

draggables.forEach((item) => {
  item.addEventListener("dragstart", () => {
    item.classList.add("is-dragging");
  });
  item.addEventListener("dragend", () => {
    item.classList.remove("is-dragging");
    const itemIdElement = item.querySelector(".id");
    const csrf_token =  item.querySelector("#csrf_token").value;
    const itemId = itemIdElement.textContent;
    const newStatus = item.parentElement.id === "tbp-lane" ? 0 : 1;

    fetch('/purchase-item/'+newStatus, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-token' : csrf_token
      },
      body: JSON.stringify({ itemId }),
    })
      .then((response) => {
        if (response.ok) {
          console.log("Item status updated successfully!");
        } else {
          console.error("Failed to update item status:", response.statusText);
        }
      })
      .catch((error) => {
        console.error("Error updating item status:", error);
      });
  });
});

droppables.forEach((zone) => {
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();

    const bottomTask = insertAboveTask(zone, e.clientY);
    const curTask = document.querySelector(".is-dragging");

    if (!bottomTask) {
      zone.appendChild(curTask);
    } else {
      zone.insertBefore(curTask, bottomTask);
    }
  });
});

const insertAboveTask = (zone, mouseY) => {
  const els = zone.querySelectorAll(".item:not(.is-dragging)");

  let closestTask = null;
  let closestOffset = Number.NEGATIVE_INFINITY;

  els.forEach((item) => {
    const { top } = item.getBoundingClientRect();

    const offset = mouseY - top;

    if (offset < 0 && offset > closestOffset) {
      closestOffset = offset;
      closestTask = item;
    }
  });

  return closestTask;
};
