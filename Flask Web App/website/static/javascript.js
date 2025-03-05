function inventory(){
    window.open("/inventory")
}

function connected_consumer(){
    window.open("/connected_consumer")
}

function add_item(){
    window.open("#divOne")
}

function show_inventory(){
    window.open("/inventory_items")
    
}

function enter_shop(shopId) {
    window.location.href = "/consumer/shop/details/" + shopId;
}

function search_items(shopId) {
    var item_name = document.getElementById('searchInput').value;
    if (item_name) {
        window.location.href = "/consumer/shop/details/" + shopId + "/search?item_name=" + item_name;
    } else {
        alert('Item name is required.');
    }
}
