import React, { useState } from 'react';
import Image from 'next/image'


function MapStyleSelector({ mapStyles, selectedStyle, handleStyleChange }) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  return (
    <div className="absolute right-32 text-slate-700 h-20 w-40
    max-sm:h-10 max-sm:w-20 max-sm:top-14 max-sm:right-0
    ">
      {/* Button to show the selected style */}
      
      <button
        className="flex right-20 items-center h-20 w-40 m-2 p-2 rounded-xl text-[12px] bg-white hover:bg-gray-200 cursor-pointer z-20
        max-sm:h-14 max-sm:w-14 max-sm:justify-center 
        "
        onClick={toggleDropdown}
      >
        {selectedStyle ? (
          <img
            src={mapStyles.find(style => style.value === selectedStyle).image}
            alt={mapStyles}
            className="w-12 h-12 m-2
            max-sm:w-10 max-sm:h-10 max-sm:p-0 max-sm:rounded-lg
            " // Adjust size as needed
          />
        ) : 'Select Style'}
        <h1 className='text-slate-700
        max-sm:hidden
        '>{mapStyles.find(style => style.value === selectedStyle).label}</h1>
      </button>

      {/* Dropdown menu */}
    
        <div className={`relative ${isDropdownOpen ?'block ':'hidden   '}  top-1 right-0 mt-2 shadow-lg z-0
        max-sm: justify-center
        `}>
          {mapStyles.map((style, index) => (
            <div
              key={index}
              className={`flex items-center   h-20 w-40 m-2 p-2 rounded-2xl text-[12px] bg-white hover:bg-gray-200 cursor-pointer
              max-sm:h-14 max-sm:w-14
              `}
              onClick={() => {
                handleStyleChange(style.value);
                setIsDropdownOpen(false);
              }}
            >
              <Image
                width={20}
                height={20}
                src={style.image}
                alt={style.label}
                className="w-14 h-14 mr-2  rounded-xl
                max-sm:h-10 max-sm:w-10 max-sm:rounded-lg
                " // Adjust size as needed
              />
              <span className='max-sm:hidden'>{style.label}</span>
            </div>
          ))}
        </div>
      
    </div>
  );
}

export default MapStyleSelector;
