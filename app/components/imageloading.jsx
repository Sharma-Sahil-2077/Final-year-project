import React, { useState, useEffect } from 'react';
// import './RandomRectanglesLoading.css'; // Import your Tailwind CSS file

const RandomRectanglesLoading = () => {
  const [currentRectangle, setCurrentRectangle] = useState(null);

  useEffect(() => {
    // Function to generate and display one random rectangle at a time
    const generateAndDisplayRectangle = () => {
      const newRectangle = {
        id: Math.random(),
        width: Math.floor(Math.random() * 50) + 100, // Random width between 100px and 400px
        height: Math.floor(Math.random() * 50) + 100, // Random height between 100px and 400px
        top: `${Math.random() * 80}%`, // Random top position
        left: `${Math.random() * 80}%`, // Random left position
      };
      setCurrentRectangle(newRectangle);

      // Timeout to clear the displayed rectangle after 5 seconds
      setTimeout(() => {
        setCurrentRectangle(null);
      }, 1000);
    };

    generateAndDisplayRectangle(); // Initial generation and display of rectangle

    // Interval to generate and display rectangles every 5 seconds
    const interval = setInterval(() => {
      generateAndDisplayRectangle();
    }, 100);

    return () => clearInterval(interval); // Clean up interval

  }, []); // Run effect only once on component mount

  return (
    <div className="absolute h-[500px] w-full left-10 top-14 z-50">
      {currentRectangle && (
        <div
          key={currentRectangle.id}
          className="absolute border-[3px] border-orange-500"
          style={{
            width: `${currentRectangle.width}px`,
            height: `${currentRectangle.height}px`,
            top: currentRectangle.top,
            left: currentRectangle.left,
          }}
        ></div>
      )}
    </div>
  );
};

export default RandomRectanglesLoading;
