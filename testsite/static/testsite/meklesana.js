// Pagaidu kods no W3Schools par range slider

var slider = document.getElementById("range");
var output = document.getElementById("cena_izvade");
output.innerHTML = slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
slider.addEventListener("input", function() {
    output.innerHTML = this.value;
});