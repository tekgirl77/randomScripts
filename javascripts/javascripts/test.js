

function add(num1,num2) {
    return num1 + num2;
}

subtract = function(num1,num2) {
    return num1 - num2;
};

console.log(subtract(10,5));

console.log("----------------");

//NaN is still considered a Number type:
var value = (add(1)); //No error thrown, and no second number to add means this results in NaN
console.log("value is: " + value);
console.log(typeof(value));
console.log(value instanceof Object);

console.log("----------------");

//Use "return arguments" to view an expression's arguments that were passed
func_expression = function() {
    return arguments
};
console.log(func_expression("hi"," there"));

console.log("----------------");

//Add and remove properties at any time - both object1 and object2 point to the same object in memory.
var object1 = Object();
var object2 = object1;
object1.customProperty = "I love JS!";
console.log(object1.customProperty);
console.log(object2.customProperty);

console.log("----------------");

//Dereference an object
object1 = null;
console.log(object1);
//object2 still points to the original immutable reference in memory
console.log(object2);

var red;

var carColor = function(color) {var colors=[]; colors.push([9,2],[2,4],[3,2]); return colors};
console.log(carColor(red).sort(function(a,b) {return a[0]-b[0]}));

console.log("----------------");

//Array.isArray() identifies whether an object is an array or not
colors = carColor(red);
console.log(Array.isArray(colors));

console.log("----------------");

//All objects, including functions, have a length property:
console.log(subtract.length); //function.length shows the number of arguments expected
console.log(colors.length);
//console.log(red.length); //Throws error if undefined
var blue = "blue";
console.log(blue.length);

console.log("----------------");

/*
gettwodoors = function(doors,color) {
    colors = carColor(color);
    var twodoorcars = [];
    for (var i = 0; i < colors.length; i++) {
        if (colors[i][1] == 2) {
            console.log("Found a red 2-door car: " + colors[i]);
            twodoorcars.push(colors[i]);}}
    return console.log(twodoorcars);};

console.log(gettwodoors(2,red));
*/

