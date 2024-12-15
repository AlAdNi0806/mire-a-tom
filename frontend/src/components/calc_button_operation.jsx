import { MathJax, MathJaxContext } from 'better-react-mathjax'
import React from 'react'

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

const CalcButtonOperation = ({ button, onClick }) => {
    return (
        <div
            onClick={() => onClick(button)}
            className='flex items-center justify-center overflow-hidden font-bold transition-all duration-300 cursor-pointer select-none min-w-14 min-h-14 max-w-14 max-h-14 ring-2 rounded-xl ring-zinc-700 hover:bg-zinc-50'
        >
            <MathJaxContext
                version={3}
                config={config}
            >
                <MathJax>
                    {`\\( \\large ${button.label}\\)`}
                </MathJax>
            </MathJaxContext>
        </div>
    )
}

export default CalcButtonOperation