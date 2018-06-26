function callChangeFunc(){
    var id = document.getElementsByName('productID')[0]['value'];
    var newPrice = document.getElementsByName('newPrice')[0]['value'];
    var params = {
        "productID": id,
        "newPrice": newPrice
    };
    $.ajax({
        url: "/core-py/changePrice",
        type: "PUT",
        contentType: "application/json",
        data: JSON.stringify(params),
        complete: function(xhr, status){
            document.getElementById("form").innerHTML = xhr.responseText;
            console.log(xhr.responseText);
        }
    });
}