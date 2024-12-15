import { useEffect, useLayoutEffect, useRef, useState } from 'react'

import { Input } from '@/components/ui/input';
import { MathJax, MathJaxContext } from "better-react-mathjax";

import CalcButton from './components/calc_button';

import 'katex/dist/katex.min.css';
import Latex from 'react-latex-next';
import { set } from 'date-fns';
import { Clipboard, MoveLeft, Search } from 'lucide-react';
import axios from 'axios';
import CalcButtonOperation from './components/calc_button_operation';
import { convertLatexToAsciiMath } from 'mathlive';

// bg-emerald-200
// bg-red-200

const config = {
  loader: { load: ["[tex]/html"] },
  tex: {
    packages: { "[+]": ["html"] },
    inlineMath: [
      ["$", "$"],
      ["\\(", "\\)"]
    ],
    displayMath: [
      ["$$", "$$"],
      ["\\[", "\\]"]
    ]
  },
};

const CALCULATOR_BUTTONS = [
  {
    label: "1",
    value: "1"
  },
  {
    label: "2",
    value: "2"
  },
  {
    label: "3",
    value: "3"
  },
  {
    label: "4",
    value: "4"
  },
  {
    label: "5",
    value: "5"
  },
  {
    label: "6",
    value: "6"
  },
  {
    label: "7",
    value: "7"
  },
  {
    label: "8",
    value: "8"
  },
  {
    label: "9",
    value: "9"
  },
  {
    label: "C",
    value: "C"
  },
  {
    label: "0",
    value: "0"
  },
  {
    label: "=",
    value: "="
  },
  {
    label: "<",
    value: "<"
  },
  {
    label: ">",
    value: ">"
  },
  {
    label: "DEL",
    value: "DEL"
  },

]

// const CALCULATOR_OPERATIONS = [
//   {
//     label: "+",
//     value: "+",
//     libraryValue: "+"
//   },
//   {
//     label: "-",
//     value: "-",
//     libraryValue: "-"
//   },
//   {
//     label: "\\cdot",
//     value: "\\cdot",
//     libraryValue: "\\cdot"
//   },
//   {
//     label: "\\div",
//     value: "\\div",
//     libraryValue: "\\div"
//   },
//   {
//     label: "√",
//     value: "\\sqrt{\\Box}",
//     libraryValue: "\\sqrt"
//   },
//   {
//     label: "x^{2}",
//     value: "x^{2}",
//     libraryValue: "^"
//   },
//   {
//     label: "\\alpha",
//     value: "\\alpha",
//     libraryValue: "\\alpha"
//   },
//   {
//     label: "b",
//     value: "\\beta",
//     libraryValue: "\\beta"
//   },
//   {
//     label: "\\frac{\\Box}{\\Box}",
//     value: "\\frac{\\Box}{\\Box}",
//     libraryValue: "\\frac"
//   },
//   {
//     label: "\\int_{\\Box}^{\\Box}",
//     value: "\\int_{\\Box}^{\\Box}",
//     libraryValue: "\\int_"
//   },
//   {
//     label: "\\int",
//     value: "\\int",
//     libraryValue: "\\int"
//   },
//   {
//     label: "\\log_{2}",
//     value: "\\log_{2}",
//     libraryValue: "\\log_{2}"
//   },


// ]

const BOX = "\\Box"


function roundToDecimalPlaces(num, decimalPlaces) {
  const factor = Math.pow(10, decimalPlaces);
  return Math.round(num * factor) / factor;
}


function App() {
  const [count, setCount] = useState(0)

  const [search, setSearch] = useState(false)
  const [searchResult, setSearchResult] = useState([])
  const [searchResultAscii, setSearchResultAscii] = useState([])

  const sampleEquation1 = "U = 1/(R_(si) + sum_(i=1)^n(s_n/lambda_n) + R_(se))";
  const sampleEquation2 = "c = a^2 + b^2";
  const sampleEquation3 = "f(a) = 1/(R_(si) + sum_(i=1)^n(s_n/lambda_n) + R_(se))";

  const [equation, setEquation] = useState(sampleEquation1);
  const [inputMode, setInputMode] = useState(false)
  const inputRef = useRef(null);

  const [label, setLabel] = useState('');
  const [value, setValue] = useState('');
  const [libraryValue, setLibraryValue] = useState('');
  const labelRef = useRef(null);
  const valueRef = useRef(null);
  const libraryValueRef = useRef(null);

  const [simplified, setSimplified] = useState(false)


  const [CALCULATOR_OPERATIONS, SET_CALCULATOR_OPERATIONS] = useState([])

  useLayoutEffect(() => {

    const requestData = async () => {
      const url = "http://127.0.0.1:5010/operations"

      const result = await axios.get(url)
      console.log(result.data)
      SET_CALCULATOR_OPERATIONS(result.data)
    }

    requestData()
  }, []);



  // const test = " \\mbox{~and~} \\left[ \\begin{array}{cc|r} 3 & 4 & 5 \\\þ 1 & 3 & 729 \\end{array} \\right]"
  // const test = "\\( \\underbrace{ \\overbrace{a+b}^6 \\cdot \\overbrace{c+d}^7 }_\\text{example of text} = 42 \\)"
  // const test = "\\( f(z) = \\left\\{ \\begin{array}{rcl} \\overline{\\overline{z^2}+\\cos z} & \\mbox{for} & |z|<3 \\ 0 & \\mbox{for} & 3\\leq|z|\\leq5 \\\ \\sin\\overline{z} & \\mbox{for} & |z|>5 \\nd{array}\\right. \\)"
  // const test = "A = \\begin{bmatrix}  	1 & 3 & 5 \\\\ 	2 & 4 & 6\\ 	\\end{bmatrix}"


  const test = " \\begin{matrix} R^n & \\overset{A}{\\longrightarrow} & R^m \\\\ \\cong &  & \\cong \\\\ R^n & \\overset{B}{\\longrightarrow} & R^m \\\\ \\end{matrix}"

  const [latex, setLatex] = useState("\\frac{1}{\\sqrt{2}}\\cdot2")
  // const [latex, setLatex] = useState("\\frac{\\color{Red} 1}{\\sqrt{2}}\\cdot2")
  // const [latex, setLatex] = useState("\\frac{\\Box}{\\Box}")
  // const [latex, setLatex] = useState("8888888")
  const [cursor, setCursor] = useState(0)

  useEffect(() => {
    let newLatex = latex;

    // console.log(newLatex.length)
    // console.log(cursor)

    if (cursor > newLatex.length) {
      setCursor(newLatex.length);
      return
    } else if (cursor < 0) {
      setCursor(0);
      return
    }

    newLatex = newLatex.split('');
    newLatex.splice(cursor, 0, "|"); // Insert at cursor position
    newLatex = newLatex.join('');

    setLatex(newLatex);
  }, [cursor])



  const findNextNumberIndex = (str, startIndex) => {
    for (let i = startIndex; i < str.length; i++) {
      if (/\d/.test(str[i])) { // Check if the character is a digit
        return i; // Return the index of the digit
      }
    }
    return -1; // Return -1 if no digit is found
  };

  const findSecondOccurrenceIndex = (str, startIndex, char) => {
    // Find the first occurrence after startIndex
    const firstIndex = str.indexOf(char, startIndex);

    // If the first occurrence is not found, return -1
    if (firstIndex === -1) {
      return -1;
    }

    // Find the second occurrence after the firstIndex
    const secondIndex = str.indexOf(char, firstIndex + 1);

    return secondIndex; // Return the index of the second occurrence, or -1 if not found
  };

  const goForward = (newLatex) => {

    let count = 0;

    newLatex = newLatex.split('');

    newLatex.splice(cursor, 1);
    newLatex = newLatex.join('');

    let updatedCursor = cursor;

    ////
    // console.log(newLatex[updatedCursor - 2], newLatex[updatedCursor - 3], newLatex[updatedCursor], newLatex)
    if (newLatex[updatedCursor] === `}`) {
      //PREV CONTENT
      if (newLatex[updatedCursor - 1] === '{') {


        const firstLatexPart = newLatex.substring(0, updatedCursor)
        const lastLatexPart = newLatex.substring(updatedCursor, newLatex.length)
        const updatedLatex = firstLatexPart + BOX + lastLatexPart
        // console.log(firstLatexPart, lastLatexPart)
        // console.log(updatedLatex)
        // console.log(prevBracesContent, isPrevBracesEmpty)
        newLatex = updatedLatex
        updatedCursor += BOX.length

      }
    }


    if (newLatex[updatedCursor + 1] === `{`) {
      updatedCursor += 1

      //NEXT CONTENT
      const nextOpenBraceIndex = newLatex.indexOf('{', updatedCursor) + 1;
      const nextCloseBraceIndex = newLatex.indexOf('}', updatedCursor + 1);
      console.log("NEXTANDPOST", nextOpenBraceIndex, nextCloseBraceIndex)

      const nextBracesContent = newLatex.substring(nextOpenBraceIndex, nextCloseBraceIndex)
      const isNextBracesEmpty = (nextBracesContent.length === 0 || nextBracesContent === undefined || nextBracesContent === BOX) ? true : false

      console.log("NEXT", isNextBracesEmpty, nextBracesContent)
      if (isNextBracesEmpty === true) {
        const firstLatexPart = newLatex.substring(0, nextOpenBraceIndex)
        const lastLatexPart = newLatex.substring(nextCloseBraceIndex, newLatex.length)
        const updatedLatex = firstLatexPart + lastLatexPart
        // console.log(firstLatexPart, lastLatexPart)
        // console.log(updatedLatex)
        // console.log(nextBracesContent, isNextBracesEmpty)
        newLatex = updatedLatex
      }
    }
    ////



    if (newLatex[updatedCursor] === `\\`) {

      count += 1

      const nextSlashIndex = findSecondOccurrenceIndex(newLatex, updatedCursor, '\\') < 0 ? 100000 : findSecondOccurrenceIndex(newLatex, updatedCursor, '\\');
      const nextNumberIndex = findNextNumberIndex(newLatex, updatedCursor) < 0 ? 100000 : findNextNumberIndex(newLatex, updatedCursor);
      const nextOpenBraceIndex = newLatex.indexOf('{', updatedCursor) === -1 ? 100000 : newLatex.indexOf('{', updatedCursor) + 1;
      const nextCloseBraceIndex = newLatex.indexOf('}', updatedCursor) === -1 ? 100000 : newLatex.indexOf('}', updatedCursor);
      const nextSpaceIndex = newLatex.indexOf(' ', updatedCursor) === -1 ? 100000 : newLatex.indexOf(' ', updatedCursor);

      console.log(nextSlashIndex, nextNumberIndex, nextOpenBraceIndex, nextCloseBraceIndex, nextSpaceIndex)


      const newClosestBraceIndex = Math.min(nextOpenBraceIndex, nextCloseBraceIndex);
      const newIndex = Math.min(newClosestBraceIndex, nextSpaceIndex);
      const newBreakIndex = Math.min(nextSlashIndex, nextNumberIndex);





      ////
      const nextBracesContent = newLatex.substring(nextOpenBraceIndex, nextCloseBraceIndex)
      const nextContent = newLatex.substring(updatedCursor, nextCloseBraceIndex)
      const isNextBracesEmpty = (nextBracesContent.length === 0 || nextBracesContent === undefined || nextBracesContent === "\\Box") ? true : false

      console.log("------------------")
      console.log(nextBracesContent)
      console.log(nextContent)
      console.log("------------------")

      if (isNextBracesEmpty === true && newBreakIndex >= newIndex && newIndex < newLatex.length) {
        const firstLatexPart = newLatex.substring(0, nextOpenBraceIndex)
        const lastLatexPart = newLatex.substring(nextCloseBraceIndex, newLatex.length)
        const updatedLatex = firstLatexPart + lastLatexPart
        // console.log(firstLatexPart, lastLatexPart)
        // console.log(updatedLatex)
        // console.log(nextBracesContent, isNextBracesEmpty)
        newLatex = updatedLatex
      }
      ////





      if (newBreakIndex < newIndex) {
        let updated = false
        const latexSubstring = newLatex.substring(updatedCursor, newBreakIndex);

        CALCULATOR_OPERATIONS.map((operation) => {
          if (latexSubstring === operation.libraryValue) {
            setCursor(newBreakIndex)
            updated = true
            return
          }
        })


        console.log(newLatex[updatedCursor - 1], newLatex[updatedCursor], newLatex[updatedCursor + 1])

      } else if (newIndex < newLatex.length) {
        setCursor(newIndex);
        updatedCursor = newIndex;


        console.log(newLatex[updatedCursor - 1], newLatex[updatedCursor], newLatex[updatedCursor + 1])

      } else {
        setCursor(newLatex.length);
      }
    }


    if (count === 0) {
      setCursor(updatedCursor + 1);
      // const latexSubstring = newLatex.substring(nextSlash, newLatex.length);
      // console.log(latexSubstring)
    } else {
      // const latexSubstring = newLatex.substring(nextSlash, newLatex.length);
      // console.log(latexSubstring)
    }


    return newLatex;
  }



  const findLastNumberIndex = (str, startIndex) => {
    for (let i = startIndex - 1; i >= 0; i--) {
      if (/\d/.test(str[i])) { // Check if the character is a digit
        return i; // Return the index of the digit
      }
    }
    return -1; // Return -1 if no digit is found
  };

  const goBack = (newLatex) => {
    let count = 0;

    newLatex = newLatex.split('');

    // Remove the character at the current cursor position
    newLatex.splice(cursor, 1);
    newLatex = newLatex.join('');

    let updatedCursor = cursor;


    const prevBraceIndex = newLatex.lastIndexOf('\\', updatedCursor - 1);
    const latexSubstring = newLatex.substring(prevBraceIndex, updatedCursor);


    ////
    console.log("======================")

    if (newLatex[updatedCursor - 1] === `}`) {
      //PREV CONTENT
      const nextOpenBracesIndex = newLatex.lastIndexOf('{', updatedCursor - 1)

      const nextBracesContent = newLatex.substring(nextOpenBracesIndex + 1, updatedCursor - 1)
      const isNextBracesEmpty = (nextBracesContent.length === 0 || nextBracesContent === undefined || nextBracesContent === BOX) ? true : false

      // console.log(nextOpenBracesIndex, nextBracesContent, isNextBracesEmpty)

      if (isNextBracesEmpty === true) {
        const firstLatexPart = newLatex.substring(0, nextOpenBracesIndex + 1)
        const lastLatexPart = newLatex.substring(updatedCursor - 1, newLatex.length)
        const updatedLatex = firstLatexPart + lastLatexPart
        // console.log(firstLatexPart, lastLatexPart)
        // console.log(updatedLatex)
        // console.log(prevBracesContent, isPrevBracesEmpty)
        newLatex = updatedLatex
        updatedCursor -= BOX.length
      }

    }


    if (newLatex[updatedCursor - 1] === `{`) {

      //PREV CONTENT
      if (newLatex[updatedCursor - 2] === '}') {
        const prevCloseBraceIndex = newLatex.indexOf('}', updatedCursor)
        const prevBracesContent = newLatex.substring(updatedCursor, prevCloseBraceIndex)
        const isPrevBracesEmpty = (prevBracesContent.length === 0 || prevBracesContent === undefined || prevBracesContent === BOX) ? true : false

        if (isPrevBracesEmpty) {
          const firstLatexPart = newLatex.substring(0, updatedCursor)
          const lastLatexPart = newLatex.substring(updatedCursor, newLatex.length)
          const updatedLatex = firstLatexPart + BOX + lastLatexPart
          // console.log(firstLatexPart, lastLatexPart)
          // console.log(updatedLatex)
          // console.log(prevBracesContent, isPrevBracesEmpty)
          newLatex = updatedLatex
          // updatedCursor -= BOX.length
        }

      } else if (newLatex[updatedCursor] === '}') {
        const firstLatexPart = newLatex.substring(0, updatedCursor)
        const lastLatexPart = newLatex.substring(updatedCursor, newLatex.length)
        const updatedLatex = firstLatexPart + BOX + lastLatexPart

        newLatex = updatedLatex
        // updatedCursor -= BOX.length + 1
      }


      //NEXT CONTENT
      const nextOpenBracesIndex = newLatex.lastIndexOf('{', updatedCursor - 2) + 1;
      const nextBracesContent = newLatex.substring(nextOpenBracesIndex, updatedCursor - 2)
      // console.log(newLatex[updatedCursor - 2], newLatex[updatedCursor - 1], newLatex[updatedCursor], newLatex[updatedCursor + 1], newLatex[updatedCursor + 2], newLatex)
      // console.log("BRACECONTENT", nextBracesContent)
      const isNextBracesEmpty = (nextBracesContent.length === 0 || nextBracesContent === undefined || nextBracesContent === BOX) ? true : false

      console.log(nextOpenBracesIndex, nextBracesContent, isNextBracesEmpty)

      if (isNextBracesEmpty === true) {
        const firstLatexPart = newLatex.substring(0, nextOpenBracesIndex)
        const lastLatexPart = newLatex.substring(updatedCursor - 2, newLatex.length)
        const updatedLatex = firstLatexPart + lastLatexPart
        // console.log(firstLatexPart, lastLatexPart)
        // console.log(updatedLatex)
        // console.log(prevBracesContent, isPrevBracesEmpty)
        newLatex = updatedLatex
        updatedCursor -= BOX.length
      }
    }
    ////

    let updated = false
    if (updatedCursor === cursor) {
      CALCULATOR_OPERATIONS.map((operation) => {
        if (latexSubstring === operation.libraryValue) {
          updated = true
          setCursor(prevBraceIndex)
        }
      })
    }



    if (updated === false) {
      if (newLatex[updatedCursor - 2] === '}' && newLatex[updatedCursor - 1] === '{') {
        updatedCursor -= 1
      } else if (newLatex[updatedCursor - 1] === '{') {
        const prevBraceIndex = newLatex.lastIndexOf('\\', updatedCursor - 1);
        updatedCursor = prevBraceIndex + 1
      }

      setCursor(updatedCursor - 1);
    }

    return newLatex;
  }



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

  const remove = (newLatex) => {
    let count = 0;

    newLatex = newLatex.split('');

    // Remove the character at the current cursor position
    newLatex.splice(cursor, 1);
    newLatex = newLatex.join('');

    let updatedCursor = cursor;


    const prevBraceIndex = newLatex.lastIndexOf('\\', updatedCursor - 1);
    const latexSubstring = newLatex.substring(prevBraceIndex, updatedCursor);

    console.log("+++++++++++++++++++++")
    console.log(latexSubstring)

    let updated = false
    if (updatedCursor === cursor) {
      CALCULATOR_OPERATIONS.map((operation) => {
        if (latexSubstring === operation.libraryValue) {
          updated = true
          const firstLatexPart = newLatex.substring(0, prevBraceIndex)
          const lastLatexPart = newLatex.substring(updatedCursor, newLatex.length)
          newLatex = firstLatexPart + lastLatexPart
          setCursor(prevBraceIndex)
        }
      })
    }

    if (updated === true) {
      return newLatex
    }


    if (newLatex[updatedCursor - 1] === '}') {

      let closeBracesCount = 0
      let latestOpenBracesIndex = updatedCursor
      let count = 0

      while (newLatex[latestOpenBracesIndex - 1] === '}') {
        count += 1

        if (closeBracesCount > 100) {
          setCursor(updatedCursor)
          return newLatex
        }

        while (newLatex[latestOpenBracesIndex - closeBracesCount - 1] === '}') {
          closeBracesCount += 1

          if (closeBracesCount > 100) {
            setCursor(updatedCursor)
            return newLatex
          }

        }

        let temporaryLatestOpenBracesIndex = findNthOccurrenceBackwardIndex(newLatex, latestOpenBracesIndex, '{', closeBracesCount);
        const prevSubString = newLatex.substring(temporaryLatestOpenBracesIndex, latestOpenBracesIndex - closeBracesCount - 1)
        if (prevSubString.includes('}')) {
          const countOccurrences = (str, char) => {
            return str.split(char).length - 1; // Split the string by the character and subtract 1
          };

          latestOpenBracesIndex = findNthOccurrenceBackwardIndex(newLatex, latestOpenBracesIndex, '{', closeBracesCount + countOccurrences(prevSubString, '}'));
        } else {
          latestOpenBracesIndex = temporaryLatestOpenBracesIndex
        }

        closeBracesCount = 0
      }

      const prevSlashIndex = newLatex.lastIndexOf('\\', latestOpenBracesIndex - 1);
      const latexSubstring = newLatex.substring(prevSlashIndex, latestOpenBracesIndex);

      let isOperation = false
      CALCULATOR_OPERATIONS.map((operation) => {
        if (latexSubstring === operation.libraryValue) {
          isOperation = true
        }
      })

      console.log(updatedCursor, closeBracesCount)
      console.log(latestOpenBracesIndex)
      const firstLatexPart = newLatex.substring(0, isOperation ? prevSlashIndex : latestOpenBracesIndex)
      const lastLatexPart = newLatex.substring(updatedCursor, newLatex.length)
      console.log(firstLatexPart, lastLatexPart)
      newLatex = firstLatexPart + lastLatexPart
      updatedCursor = isOperation ? prevSlashIndex : latestOpenBracesIndex

    } else if (newLatex[updatedCursor - 1] === '{') {

    } else {
      const firstLatexPart = newLatex.substring(0, updatedCursor - 1)
      const lastLatexPart = newLatex.substring(updatedCursor, newLatex.length)
      console.log(firstLatexPart, lastLatexPart)
      newLatex = firstLatexPart + lastLatexPart
      updatedCursor -= 1
    }





    if (updated === false) {
      setCursor(updatedCursor);
    }

    return newLatex;
  }


  // const latexRef = React.useRef(latex);
  // latexRef.current = latex;
  useEffect(() => {
    const handleKeyDown = (event) => {
      // do not allow when a input is focused
      if (inputMode === false && document.activeElement !== labelRef.current && document.activeElement !== valueRef.current && document.activeElement !== libraryValueRef.current) {
        switch (event.key) {
          case 'ArrowRight':
            onClick({ value: ">" }, event);
            break;
          case 'ArrowLeft':
            onClick({ value: "<" }, event);
            break;
          case 'Backspace':
            onClick({ value: "DEL" }, event);
            break;
          default:
            break;
        }
      }
    };

    // Add event listener for keydown
    window.addEventListener('keydown', handleKeyDown);

    // Cleanup the event listener on component unmount
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [latex, inputMode]);

  const onClick = (button) => {
    // console.log(button)
    // let newLatex = latex.replace(/\^/g, '');
    if (inputMode === true) {

    }

    let newLatex = latex;
    console.log("called++++++++++++++++++++++++++++++++++++++++", newLatex)

    if (button.value === "C") {
      newLatex = "";
      setCursor(0);
    } else if (button.value === "<") {
      newLatex = goBack(newLatex);
    } else if (button.value === ">") {
      newLatex = goForward(newLatex)
    } else if (button.value === "DEL") {
      if (newLatex[cursor - 1] !== '{') {
        newLatex = remove(newLatex)
      }
    } else {
      newLatex = newLatex.split(''); // Convert string to array
      newLatex.splice(cursor + 1, 0, button.value); // Update the specific index
      newLatex = newLatex.join('');
      newLatex = goForward(newLatex)
      // setCursor(cursor + button.value.length);
    }

    setLatex(newLatex);
  }


  const [isCopied, setIsCopied] = useState(false);

  const handleClick = () => {
    // Copy the text to the clipboard
    const copyLatex = latex.replace(/\|/g, '')
    navigator.clipboard.writeText(copyLatex).then(() => {
      // Change the background color to black
      setIsCopied(true);

      // Reset the background color after 1.5 seconds
      setTimeout(() => {
        setIsCopied(false);
      }, 1500);
    });
  };




  const onSearch = async () => {
    setSearch(true)

    let newLatex = latex;
    newLatex = newLatex.split(''); 
    newLatex[cursor] = ""; 
    newLatex = newLatex.join('');
    console.log("**********************************");
    const latexToAscii = convertLatexToAsciiMath(newLatex);
    console.log(convertLatexToAsciiMath(latexToAscii));
    console.log("**********************************");


    const url = "http://127.0.0.1:5010/submit"

    const formulasUrl = "http://127.0.0.1:5010/get_formulas"
    const formulas = await axios.post(formulasUrl)
    const formulasInAscii = formulas.data.map(formula => convertLatexToAsciiMath(formula))


    const data = {
      formula: newLatex,
      latexToAscii: latexToAscii,
      formulas: formulasInAscii
    }


    const result = await axios.post(url, data)
    const analysisAccendingBySimilarity = result.data.analysis.sort((a, b) => b.similarity - a.similarity)
    const analysisAccendingBySimilarityAscii = result.data.latexToAsciiAnalysis.sort((a, b) => b.similarity - a.similarity)
    setSearchResult(analysisAccendingBySimilarity)
    setSearchResultAscii(analysisAccendingBySimilarityAscii)
    console.log(result)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (label === '' || value === '' || libraryValue === '') {
      alert("Пожалуйста, заполните все поля")
      return
    } else if (value.includes(BOX) || libraryValue.includes(BOX)) {
      alert("Не должно быть в значении \\Box")
      return
    } else if (value.includes('|') && libraryValue.includes('|')) {
      alert("Не должно быть в значении |")
      return
    }
    console.log(label, value, libraryValue)
    const data = {
      label: label.replace(/ /g, ''),
      value: value.replace(/ /g, ''),
      libraryValue: libraryValue.replace(/ /g, '')
    };
    const url = "http://127.0.0.1:5010/add_operation"
    const result = await axios.post(url, data)
    if (result.data.status === "success") {
      setLabel('')
      setValue('')
      setLibraryValue('')
      setSearch(false)

      const operationsUrl = "http://127.0.0.1:5010/operations"

      const operationsResult = await axios.get(operationsUrl)
      console.log(operationsResult.data)
      SET_CALCULATOR_OPERATIONS(operationsResult.data)
    } else {
      alert("Ошибка добавления операции")
    }

  }




  return (
    <div className='w-screen h-screen p-8 pt-4 overflow-x-hidden overflow-y-auto'>



      <div className='flex flex-col items-center justify-center gap-4 py-4 overflow-hidden rounded-lg ring-2 ring-zinc-400 min-h-32 max-h-32'>
        <MathJaxContext
          version={3}
          config={config}
        >
          <MathJax>
            {`\\( \\Huge ${latex}\\)`}
          </MathJax>
        </MathJaxContext>
      </div>

      {search === false && (
        <label className="inline-flex items-center gap-4 mt-4 mb-4 cursor-pointer">
          <div>Режим ввода</div>
          <input
            ref={inputRef}
            type="checkbox"
            value={inputMode}
            onChange={() => {
              if (inputMode === true) {
                goForward(latex)
                goBack(latex)
              } else {
                setLatex(latex.replace(/\|/g, ''))
              }
              setInputMode(!inputMode)
            }}
            onFocus={(e) => e.preventDefault()} // Prevent default scrolling
            className="hidden"
          />
          <div className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${inputMode ? 'bg-stone-500' : 'bg-stone-200'}`}>
            <div className={`absolute top-[0.115rem] left-1 w-5 h-5 rounded-full transition-transform duration-200 ${inputMode ? 'translate-x-4 bg-white' : 'bg-stone-500'}`}></div>
          </div>
        </label>
      )}


      {inputMode === true && search === false ? (
        <div className='flex items-center w-full gap-4 mt-4 mb-12'>
          <Input
            value={latex}
            onChange={(e) => setLatex(e.target.value)}
          />
          {search === false && (
            <div
              onClick={() => onSearch()}
              className='flex items-center justify-center gap-4 p-2 px-6 overflow-hidden text-xl font-semibold text-blue-500 transition-all duration-300 bg-blue-100 rounded-lg cursor-pointer flex-nowrap w-max min-h-14 min-w-14 max-h-14 hover:bg-blue-200'
            >
              Поиск
              <Search className=' stroke-6 min-w-6' />
            </div>
          )}
        </div>
      ) : (
        <div className='flex items-center w-full gap-4 mt-4 mb-12'>
          {search === true && (
            <div
              onClick={() => setSearch(false)}
              className='flex items-center justify-center p-2 font-semibold transition-all duration-300 rounded-lg cursor-pointer min-w-14 min-h-14 bg-zinc-100 hover:bg-zinc-200 w-max'
            >
              <MoveLeft />
            </div>
          )}
          <div
            onClick={handleClick}
            className={`flex justify-center items-center w-full relative text-center text-lg cursor-pointer font-semibold rounded-lg py-4 transition-all duration-300 ${isCopied ? 'bg-zinc-300' : 'hover:bg-zinc-200 text-zinc-600 bg-zinc-100'}`}
          >
            <Clipboard className='absolute text-black align-middle right-4' />
            {latex}
          </div>
          {search === false && (
            <div
              onClick={() => onSearch()}
              className='flex items-center justify-center gap-4 p-2 px-6 overflow-hidden text-xl font-semibold text-blue-500 transition-all duration-300 bg-blue-100 rounded-lg cursor-pointer flex-nowrap w-max min-h-14 min-w-14 max-h-14 hover:bg-blue-200'
            >
              Поиск
              <Search className=' stroke-6 min-w-6' />
            </div>
          )}
        </div>
      )}

      {search === true && (
        <div>
          <div className='mb-4 -mt-8 text-3xl font-semibold'>
            Results:
          </div>
          <label className="inline-flex items-center gap-4 mt-4 mb-4 cursor-pointer">
            <div>Спавнивание по упрощению</div>
            <input
              ref={inputRef}
              type="checkbox"
              value={simplified}
              onChange={() => {
                setSimplified(!simplified)
              }}
              onFocus={(e) => e.preventDefault()} // Prevent default scrolling
              className="hidden"
            />
            <div className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${simplified ? 'bg-stone-500' : 'bg-stone-200'}`}>
              <div className={`absolute top-[0.115rem] left-1 w-5 h-5 rounded-full transition-transform duration-200 ${simplified ? 'translate-x-4 bg-white' : 'bg-stone-500'}`}></div>
            </div>
          </label>
        </div>
      )}
      {search === true && searchResult.length > 0 && simplified === true && searchResultAscii.map(result => (
        <div key={result.id} className='flex flex-col gap-4 p-2 mb-6 rounded-md bg-zinc-100'>
          <div className='p-4 text-xl font-semibold'>
            <MathJaxContext
              version={3}
              config={config}
            >
              <MathJax>
                {`\\( \\large ${result.formula}\\)`}
              </MathJax>
            </MathJaxContext>
          </div>
          <div className='flex gap-2'>
            <div>
              {result.differences.split(/(?=[+-])|(?<=[+-])/).map((part, index) => {
                if (part === '+' || part === '-') {
                  return null;
                }
                const sign = result.differences[result.differences.indexOf(part) - 1];
                console.log(result.formula, sign)
                return (
                  <span key={index} className={`${(sign === '+' || !sign) ? 'bg-emerald-200' : 'bg-red-200'}`}>
                    {part.trim()}
                  </span>
                );
              })}
            </div>
            <div className='px-3 ml-4 font-semibold text-purple-500 bg-purple-200 rounded-md ring-2 ring-purple-500'>
              {roundToDecimalPlaces(result.similarity, 2)}%
            </div>
          </div>
          {result.differences}
        </div>
      ))}
      {search === true && searchResult.length > 0 && simplified === false && searchResult.map(result => (
        <div key={result.id} className='flex flex-col gap-4 p-2 mb-6 rounded-md bg-zinc-100'>
          <div className='p-4 text-xl font-semibold'>
            <MathJaxContext
              version={3}
              config={config}
            >
              <MathJax>
                {`\\( \\large ${result.formula}\\)`}
              </MathJax>
            </MathJaxContext>
          </div>
          <div className='flex gap-2'>
            <div>
              {result.differences.split(/(?=[+-])|(?<=[+-])/).map((part, index) => {
                if (part === '+' || part === '-') {
                  return null;
                }
                const sign = result.differences[result.differences.indexOf(part) - 1];
                console.log(result.formula, sign)
                return (
                  <span key={index} className={`${(sign === '+' || !sign) ? 'bg-emerald-200' : 'bg-red-200'}`}>
                    {part.trim()}
                  </span>
                );
              })}
            </div>
            <div className='px-3 ml-4 font-semibold text-purple-500 bg-purple-200 rounded-md ring-2 ring-purple-500'>
              {roundToDecimalPlaces(result.similarity, 2)}%
            </div>
          </div>
          {result.differences}
        </div>
      ))}





      {search === false && (
        <div className='flex gap-16'>
          <div className='grid grid-cols-3 gap-4'>
            {CALCULATOR_BUTTONS.map((button) => (
              <CalcButton
                button={button}
                onClick={onClick}
                inputMode={inputMode}
              />
            ))}
          </div>
          <div className='grid grid-cols-6 gap-4 h-min'>
            {CALCULATOR_OPERATIONS.map((button) => (
              <CalcButtonOperation
                button={button}
                onClick={onClick}
              />
            ))}
          </div>

          <form className='ml-12' onSubmit={handleSubmit}>
            <div className='mb-6 text-xl font-semibold'>
              Добавить символ
            </div>
            <div className='flex flex-col gap-4'>
              <label>
                <span className='text-sm'>Label:</span>
                <Input
                  type="text"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  className='w-64'
                  placeholder='\frac{2}{2}'
                  required
                  ref={labelRef}
                />
              </label>
              <label>
                <span className='text-sm'>Value:</span>
                <Input
                  type="text"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  className='w-64'
                  placeholder='\frac{x}{y}'
                  required
                  ref={valueRef}
                />
              </label>
              <label>
                <span className='text-sm'>Library value:</span>
                <Input
                  type="text"
                  value={libraryValue}
                  onChange={(e) => setLibraryValue(e.target.value)}
                  className='w-64'
                  placeholder='\frac'
                  required
                  ref={libraryValueRef}
                />
              </label>
            </div>
            <div
              onClick={handleSubmit}
              className='px-4 py-2 mt-6 text-white transition-all duration-300 bg-black rounded-md cursor-pointer select-none hover:bg-zinc-700'
            >
              Добавить
            </div>
            {/* <div className='text-sm text-zinc-600'>Будьте внимательны! </div> */}
          </form>
        </div>
      )}


    </div>

  )
}

export default App





