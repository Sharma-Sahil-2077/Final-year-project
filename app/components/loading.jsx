'use client';
import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid'; // For generating unique keys
import './loading.css'; // Import your Tailwind CSS file

const LoadingAnimation = () => {
  const [dots, setDots] = useState([]);

  useEffect(() => {
    // Function to generate random dots
    const generateDots = () => {
      const newDots = Array.from({ length: 20 }, () => ({
        id: uuidv4(),
        top: `${Math.random() * 98}%`, // Random top position
        left: `${Math.random() * 98}%`, // Random left position
        animationDelay: `${Math.random() * 1}s`, // Random animation delay
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
    <div className="relative h-screen flex items-center justify-center bg-black bg-opacity-60 backdrop-blur-[2px]">
    
      <div className="absolute w-[900px] h-1 bg-gray-100 animate-line"></div> {/* Horizontal line */}
      {dots.map(dot => (
        <div
          key={dot.id}
          className="absolute w-2 h-2 bg-white rounded-full animate-dot "
          style={{ top: dot.top, left: dot.left, animationDelay: dot.animationDelay }}
        ></div>
      ))}
    </div>
  );
};

export default LoadingAnimation;
