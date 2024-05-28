'use client';
import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid'; // For generating unique keys
import './small.css'; // Import your Tailwind CSS file

const Sloading = () => {
  const [dots, setDots] = useState([]);

  useEffect(() => {
    // Function to generate random dots
    const generateDots = () => {
      const newDots = Array.from({ length: 5 }, () => ({
        id: uuidv4(),
        top: `${Math.random() * 90}%`, // Random top position
        left: `${Math.random() * 90}%`, // Random left position
        animationDelay: `${Math.random() * 0}s`, // Random animation delay
      }));
      setDots(newDots);
    };

    generateDots(); // Initial generation of dots

    // Interval to regenerate dots every 5 seconds
    const interval = setInterval(() => {
      generateDots();
    }, 5000);

    return () => clearInterval(interval); // Clean up interval

  }, []); // Run effect only once on component mount

  return (
    <div className="relative h-[340px] w-[600px] flex items-center justify-center backdrop-blur-[4px] rounded-xl scale-105 object-contain">
    
      <div className="absolute w-[400px] h-1 bg-gray-100 animate-line"></div> {/* Horizontal line */}
      {dots.map(dot => (
        <div
          key={dot.id}
          className="absolute w-1.5 h-1.5 bg-white rounded-full animate-dot "
          style={{ top: dot.top, left: dot.left, animationDelay: dot.animationDelay }}
        ></div>
      ))}
      
    </div>
  );
};

export default Sloading;
