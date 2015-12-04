/**
 * Created by Salle on 11/25/15.
 */
/**
 Slightly modified version
 of the anagram found on Stackoverflow.
 @see: http://stackoverflow.com/a/16577324/1707987
 - Replaced str.substr with str.charAt
 - Cached the length of the first string
 - Check the cached len against match counter
 */

function anagram(word) {
    var anagrams = ["kiln", "link", "lead", "deal", "petals", "staple"];
    console.log("All anagrams are: \n" + anagrams.sort().join("\n"));


    for (i = 0; i < anagrams.length; i++) {
        console.log("Checking " + word + " against: " + anagrams[i] );
        if (word == anagrams[i]) {
            console.log("-----------------");
            console.log("You got it! \n" + "Your guess: " + word + "\nThe anagram: " + anagrams[i])
        }
    }
}

anagram("petals");

console.log("---------------");

console.log(anagram.isPrototypeOf(this.anagram));

console.log("------------------");
function getProperties(c) {
    for (property in c) {
        var property;
        console.log("property is: " + property);
        console.log("value is: " + c[property]);
    }
}
console.log(getProperties(anagram));


console.log(Object.keys(anagram));

console.log("------------------");
console.log(anagram.constructor.toString());


    /*
    if (typeof word === 'string' && word === anagram) {
        return true;
    }

    if (letters.length !== anagram.length) {
        return false;
    }

    var letter = null;
    var i = 0;
    var n = a.length;
    var matches = 0;
    var idx = 0;

    while(i < n) {

        letter = letters.charAt( (i += 1) );

        idx = b.indexOf(c);

        if (idx < 0) {
            return false;
        }

        s2 = b.substr(0, idx) + b.substr( (idx += 1) );

        matches += 1;
    }

    return matches === n;
}
*/
