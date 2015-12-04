/**
 * Created by Salle on 11/26/15.
 */

A = [-1, 3, -4, 5, 1, -6, 2, 1];

function solution(A) {
    var length = A.length,
        total = 0,
        i,j;
    for (i in A) {
        total += A[i];
        //if total === (remaining sum of A) then add to new array
    }
    return total;
}

console.log(solution(A));




/*
    A.forEach(function())

    }//((length + 1) /2) * (length + 2);
    var sumMinusMissing = 0;
    for (i = 0; i < length; i++) {
        sumMinusMissing += A[i];
    }
    return sum - sumMinusMissing;
}

console.log(solution(A));
*/
