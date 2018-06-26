function callDelFunc(){
    var id = document.getElementsByName('productID')[0]['value'];
    var params = {
        "productID": id
    };
    $.ajax({
        url: "/core-py/deleteProduct",
        type: "DELETE",
        contentType: "application/json",
        data: JSON.stringify(params),
        complete: function(xhr, status){
            document.getElementById("form").innerHTML = xhr.responseText;
            console.log(xhr.responseText);
        }
    });
}