function callAddFunc(){
    var id = document.getElementsByName('productID')[0]['value'];
    var category = document.getElementsByName('category')[0]['value'];
    var price = document.getElementsByName('price')[0]['value'];
    var params = {
        "productID": id,
        "category": category,
        "price": price
    };
    $.ajax({
        url: "/core-py/addProduct",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(params),
        complete: function(xhr, status){
            document.getElementById("form").innerHTML = xhr.responseText;
            console.log(xhr.responseText);
        }
    });
}