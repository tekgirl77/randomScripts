/**
 * Created by Salle on 12/3/15.
 */

/*jslint node: true */
"use strict";

// In base -2, integers are represented by sequences of bits ordered from the
// least to the most significant. The resulting base -2 integer from sequence A
// of N bits is computed by: sum{ A[i]&(-2)^i for i = 0..N-1 }.

// Assumptions:
// A is an integer within the range [0..100,000]
// Each element of the sequence array is an integer with a value of 1 or 0.

var sum,
    solution,
    A = [1, 0, 0, 1, 1]; //9
    //A = [1, 1, 0, 1]; //-9
    //A = [1, 0, 0, 1, 1, 1]; //-23
    //A = [1, 1, 0, 1, 0, 1, 1]; //23
    //A = [1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0];


sum = function (A) {
    'use strict';
    var X = 0,
        Y = 0,
        i,
        result;
    // Given an array of zero-indexed M bits, calculate representation of base -2 integer X:
    for (i = 0; i < A.length; i++) {
        X += A[i] * Math.pow(-2, i);
    }
    // Set our target Y as negative X:
    if (X <= 100000 || X >= -100000) {
        Y = -X;
    } else {
        console.log("X is: " + X);
        console.log("Please input a base which results in a base10 integer between -100,000 to 100,000");
    }
    // ***Future functionality - add to hash table or db with max (X && Y <= 100000) and (X && Y >= -100000);
    // Function to calculate and return the shortest sequence of bits representing -X.
    // We will count up to a max of 2048 in binary, compute base -2 algorithm, and
    // compare to Y for a target match:
    result = function (Y) {
        var count = 1,
            j,
            results = [],
            sum = 0;
        // Function to convert our count to binary:
        function dec2bin(dec){
            return (dec).toString(2).split("");
        }
        while (count < 300000) {
            results = dec2bin(count);
            console.log("Base10 and Base2 count are: " + count + " : " + results);
            // Start at the top of the array to find the first '1',
            // so we can slice off trailing 0's before computing algorithm:
            for (j = results.length - 1; j--;) {
                // If '1' is already the last bit in the array, no slice needed.
                if ((results[j] === 1) && (j = results.length-1)) {
                    break;
                // Else once we hit the first '1', slice off the trailing 0's
                // from end of array:
                } else if (results[j] === 1) {
                    results = results.slice(0, j + 1);
                    break;
                    }
            }
            // Loop through spliced binary and compute base -2 algorithm to compare
            // to our target Y integer:
            for (var k = 0; k < results.length; k++) {
                sum += results[k] * Math.pow(-2, k);
                console.log("Checking results... " + sum);
                if (sum === Y) {
                    console.log("Final results are: ", results);
                    return results;
                }
            }
            // If no match for our target Y integer, increase count and loop again
            count++;
        }
    };
    result = result(Y);
    return Y + " : " + result;
};

solution = sum(A);
console.log("Final result: " + solution);