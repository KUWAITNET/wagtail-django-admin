{% load wagtailadmin_tags %}
function createElementFromHTML(htmlString) {
    var div = document.createElement('div');
    div.innerHTML = htmlString.trim();

    // Change this to div.childNodes to support multiple top-level nodes.
    return div.firstChild;
}
function insertAfter(newNode, existingNode) {
    existingNode.parentNode.insertBefore(newNode, existingNode.nextSibling);
}
function addSideMenuElement(id, icon, content, href) {
    let sidbarSearch = $('form[role="search"]')[0];

    let newSideMenulement = createElementFromHTML(`<a id="${id}" class="sidebar-menu-item__link ">${icon}<span class="menuitem-label">${content}</span></a>`)
    newSideMenulement.href = href;
    let liElement = document.createElement('li');
    liElement.classList.add('sidebar-menu-item')
    liElement.appendChild(newSideMenulement);
    insertAfter(liElement, sidbarSearch);
}
addEventListener("DOMContentLoaded", (event) => {
    changeLangElementID = 'change-lang';
    changeLangElementHref = '{% url "switch_lang" %}';
    changeLangElementIcon = '{% icon name="site" class_name="messages-icon" %}';
    changeLangElementContent = '{{ other_lang }}';

    addSideMenuElement(changeLangElementID, changeLangElementIcon, changeLangElementContent, changeLangElementHref)
});