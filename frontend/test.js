// const findNextNumberIndex = (str, startIndex) => {
//     for (let i = startIndex; i < str.length; i++) {
//       if (/\d/.test(str[i])) { // Check if the character is a digit
//         return i; // Return the index of the digit
//       }
//     }
//     return -1; // Return -1 if no digit is found
//   };

//   // Example usage
//   const newLatex = "This is a test string with numbers 1, 2, 3, and 3 again.";
//   const cursorIndex = 10; // Example cursor position (after 'a' in "a test")
//   const nextNumberIndex = findNextNumberIndex(newLatex, cursorIndex);

//   console.log(nextNumberIndex, newLatex[nextNumberIndex]); // This will output the index of the next number after the cursor




const findNthOccurrenceBackwardIndex = (str, startIndex, char, occurrence) => {
  let currentIndex = startIndex;
  let count = 0;

  while (count < occurrence) {
    currentIndex = str.lastIndexOf(char, currentIndex - 1); // Search backward

    // If the character is not found, return -1
    if (currentIndex === -1) {
      return -1;
    }

    count++; // Increment the occurrence count
  }

  return currentIndex; // Return the index of the nth occurrence found
};

// Example usage:
const str = "hello world, hello universe";
const index = findNthOccurrenceBackwardIndex(str, 15, 'o', 2); // Find the 1st occurrence of 'o' backward from index 15
console.log(index); // Output: 4
