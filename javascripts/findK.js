/**
 * Created by Salle on 11/26/15.
 */

/*jslint node: true */
"use strict";

/* An integer X and a non-empty zero-indexed array A consisting of N integers are
 * given.  We want to know which elements of A are equal to X and which are different
 * from X.
 *
 * The goal is to split the array A into two parts, such that the number of elements
 * equal to X in the first part is the same as the number of elements different
 * from X in the other part.
 *
 * More formally, we are looking for a number K such that:
 * * 0 <= K <= N, and
 * * the number of elements eual to X in A[0..K-1] is the same as the number of
 * * elements different from X in A[K...N-1].
 * * K = 0 if A[0..K-1] does not contain any elements.
 * * For K = N, A[K..N-1] does not contain any elements.
 *
 * For example, given integer X = 5 and array A such that:
 * A = [5, 5, 1, 7, 2, 3, 5]
 * K = 4, because:
 * * Two of the elements of A[0-3] are equal to X, and
 * * Two of the elements of A[4-6] are different from X.
 *
 * Write a function that given an integer X and a non-empty zero-indexed array A
 * consisting of N integers, returns the value of number K satisfying the above
 * conditions.  It can be shown such index K always exists and is unique.
 *
 * Assumptions:
 * * N is an integer within the range [1..100,000];
 * * X is an integer within the range [1..100,000];
 * * Each element of array A is an integer within the range [0..100,000].
 */

//var A = [5, 5, 1, 7, 2, 3, 5];
//var A = [3, 4, 5, 6, 6, 6, 7, 8, 9, 3];
//var A = [9, 8, 3, 7, 2, 8, 0, 1, 1, 0, 3, 4, 6, 7, 2, 8, 9, 1, 0, 3, 4, 5, 6, 9, 2];
var A = [25, 2.50, 25, 25, 50, 75, 100, 75, 75, 1.25];

function solution(X, A) {
    var i, j, K,
        max = A.length,
        firstArray = [],
        secondArray = [],
        match = [],
        nonMatch = [];

    if ((max < 1 || max > 100000) || (X < 1 || X > 100000)) {
        return console.log("Please supply an integer X and an array A which is " +
            "within the range: [1..100,000]");
    }

    while (max--) {
        match = [];
        nonMatch = [];
        firstArray = A.slice("", max);
        secondArray = A.slice(max);
        console.log("--------------------------");
        console.log("Created firstArray: ", firstArray +
                    "\nCreated secondArray: ", secondArray +
                    "\nSearching for K...");
        // Search firstArray for matches to X:
        for (i in firstArray) {
            if (firstArray[i] === X) {
                match.push(firstArray[i]);
            }
        }
        // If no matches to X, then K is 0.
        if (match.length === 0) {
            return console.log("K is 0. Try again!");
        }
        // Search secondArray for integers that do NOT match X:
        for (j in secondArray) {
            if (secondArray[j] !== X) {
                nonMatch.push(secondArray[j]);
            }
        }
        /* Searching for an equal number of matches (N === X) to nonMatches (N !=== X)
         * and adding the total (matches + nonMatches) to determine K.
         */
        if (match.length === nonMatch.length) {
            K = match.length + nonMatch.length;
            return console.log("Found it!" +
                                "\nArray A was: ", A +
                                "\nInteger X was: ", X +
                                "\nK is: ", K);
        }
    }
}

solution(25, A);