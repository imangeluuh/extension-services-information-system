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
    const previousStatus =  item.querySelector(".previous-status");
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
          response.json().then((data) => {
              // Check if the item is moved to other board
              if (previousStatus.textContent != newStatus) {
                // If item is moved in purchased board, subtract the amount to the remaining balance
                if (newStatus == 1) {
                  if (window.remainingInternal > 0 ) {
                      window.remainingInternal -= data.amount
                      if (window.remainingInternal < 0) {
                        let remaining = Math.abs(remainingInternal);
                        window.remainingInternal = 0;
                        window.remainingExternal -= remaining;
                    }
                  } else {
                    window.remainingExternal -= data.amount
                  }
                } else { 
                  // If item is moved in to be purchased board, add the amount to the remaining balance
                  if (window.remainingExternal < window.externalBudget) {
                    window.remainingExternal =Number( window.remainingExternal) + Number(data.amount);
                    if (window.remainingExternal > window.externalBudget) {
                      // Add the excess in external amount to internal budget
                      let amount = window.remainingExternal - window.externalBudget;
                      window.remainingExternal = window.externalBudget;
                      window.remainingInternal = Number(window.remainingInternal) + Number(amount);
                    }
                  } else {
                    window.remainingInternal = Number(window.remainingInternal) + Number(data.amount);
                  }
                }
                // Assign the new status to previousStatus element
                previousStatus.textContent = newStatus;
                window.option.series[0].data[1].value = window.remainingInternal;
                window.option.series[0].data[0].value = window.remainingExternal;
                // Display the chart using the configuration items and data just specified.
                window.myChart.setOption(window.option);
              }
            });
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

    const bottomItem = insertAboveItem(zone, e.clientY);
    const curItem = document.querySelector(".is-dragging");

    if (!bottomItem) {
      zone.appendChild(curItem);
    } else {
      zone.insertBefore(curItem, bottomItem);
    }
  });
});

const insertAboveItem = (zone, mouseY) => {
  const els = zone.querySelectorAll(".item:not(.is-dragging)");

  let closestItem = null;
  let closestOffset = Number.NEGATIVE_INFINITY;

  els.forEach((item) => {
    const { top } = item.getBoundingClientRect();

    const offset = mouseY - top;

    if (offset < 0 && offset > closestOffset) {
      closestOffset = offset;
      closestItem = item;
    }
  });

  return closestItem;
};
