/**
 * Created by Salle on 11/26/15.
 */


//var A = [5,5,1,7,2,3,5];
var A = [3,4,5,6,6,6,7,8,9,3];

function solution(X, A) {
    var i, j, K,
        max = A.length;

    //for (max; max--;) {
    while (max--) {
        var firstArray = A.slice("", max);
        var secondArray = A.slice(max);
        var match = [];
        var nonMatch = [];
        console.log("--------------------------");
        console.log("first: ", firstArray);
        console.log("second: ", secondArray);
        console.log("searching for K...")
        for (i in firstArray) {
            console.log("i is: ", i);
            if (firstArray[i] == X) {
                match.push(firstArray[i]);
            }
        }
        if (match.length === 0) {
            return console.log("K is 0. Try again!")
        }
        for (j in secondArray) {
            console.log("j is: ", j);
            if (secondArray[j] != X) {
                nonMatch.push(secondArray[j]);
            }
        }
        if (match.length == nonMatch.length) {
            K = match.length + nonMatch.length;
            console.log("match array is: ", match);
            console.log("nonMatch array is: ", nonMatch);
            return console.log("K is: ", K);
        }
    }
}

solution(6,A);