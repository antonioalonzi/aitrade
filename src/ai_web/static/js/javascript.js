function showExpandablePopup(text) {
    console.log(document.getElementById('expandablePopup'))
    document.getElementById('expandablePopup').style.display = 'flex';
    console.log(document.getElementById('expandablePopupText'))
    document.getElementById('expandablePopupText').innerText = text;
}

function closeExpandablePopup() {
    document.getElementById('expandablePopup').style.display = 'none';
}

window.onclick = function(event) {
    let modal = document.getElementById('expandablePopup');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}