import { ChevronLeft, ChevronRight, Delete } from 'lucide-react';
import React from 'react';

const CalcButton = ({ button, onClick, inputMode }) => {
    if (inputMode && (button.label === "<" || button.label === ">" || button.label === "DEL")) {
        return null;
    }

    const renderIcon = () => {
        switch (button.label) {
            case '<':
                return <ChevronLeft className='text-black' />;
            case '>':
                return <ChevronRight className='text-black' />;
            case 'DEL':
                return <Delete className='text-black' />;
            default:
                return button.label;
        }þ
    };

    return (
        <div
            onClick={() => onClick(button)}
            className='flex items-center justify-center overflow-hidden font-bold transition-all duration-300 cursor-pointer select-none min-w-14 min-h-14 max-w-14 max-h-14 ring-2 rounded-xl ring-zinc-700 hover:bg-zinc-50'
        >
            {renderIcon()}
        </div>
    );
};

export default CalcButton;
