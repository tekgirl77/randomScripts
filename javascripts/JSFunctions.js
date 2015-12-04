/**
 * Created by Salle on 11/25/15.
 */

"use strict";
var ourBuddy = {
    name: "Geronimo",
    nicknames: ["Ger", "Geronimooo", "Buddy"],
    type: "African Grey Parrot",
    sayName: function () {
        console.log("Hi! My name is " + this.name + ".");
    },
    sayNickname: function(index) {
        console.log("Sometimes people say \"hey " + this.nicknames[index] + "!\"")
    },
    sayAllNicknames: function() {
        console.log("These are all of my nicknames: " + this.nicknames)
    }

};

console.log("-----------------");

console.log(ourBuddy.sayName());
console.log(ourBuddy.sayNickname(1));
console.log(ourBuddy.sayAllNicknames());

console.log("-----------------");

ourBuddy.nicknames.forEach(function(value, index) {
 console.log(value, index)
});


console.log("-----------------");
ourBuddy.color = "grey";
console.log(ourBuddy.color);
console.log("color" in ourBuddy); //true
console.log(ourBuddy.hasOwnProperty("color")); //true
console.log(ourBuddy.hasOwnProperty("toString")); //false
console.log("toString" in ourBuddy); //true

console.log("-----------------");

//The for-in loop enumerates prototype properties
for (var property in ourBuddy) {
    if (ourBuddy.hasOwnProperty(property)) {
        console.log(property, ":", ourBuddy[property]);
    }

}

console.log("-----------------");

//Object.keys() returns only own instance properties
var properties = Object.keys(ourBuddy);
console.log("Properties are: " + properties);

console.log("-----------------");

var i, len;

for (i=0, len=properties.length; i < len; i++) {
    console.log("Name: " + properties[i]);
    console.log("Value: " + ourBuddy[properties[i]]);
    console.log("Is property enumerable? " + ourBuddy.propertyIsEnumerable(properties[i]))
}

console.log("-----------------");


//Accessor properties are most useful when you want the assignment of a value
//to trigger some sort of behavior, or when reading a value requires the calculation
//of the desired return value. i.e. Check database to see if inventory exists.
var ourLady = {
    _name: "Cadi",
    _nickname: "stinky",
    _color: "Black & Tan",
    _breed: "German Shepherd",
    get name() {
        console.log("Reading name..." + this._name);
    },
    set name(value) {
        console.log("Setting name to %s", value);
        this._name = value;
    }
};

console.log(ourLady.name); //Reading name... Cadi
ourLady.name = "new dog Bowser"; //Setting name
console.log(ourLady.name); //Reading new name - new dog Bowser


