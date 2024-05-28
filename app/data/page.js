'use client';
import React, { useEffect, useRef, useState } from 'react';
import './grid.css';

const GridAnimation = () => {
  const [boxes, setBoxes] = useState(
    Array.from({ length: 20 }, () =>
      Array.from({ length: 20 }, () => 1)
    )
  );

  useEffect(() => {
    const interval = setInterval(() => {
      setBoxes(prevBoxes => {
        const newBoxes = prevBoxes.map(row =>
          row.map(scale => {
            if (Math.random() < 0.02) { // 10% chance to change the scale
              return scale === 1 ? 1.2 : 0.8;
            }
            return scale;
          })
        );
        return newBoxes;
      });
    }, 300);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid-container bg-white">
      {boxes.map((row, rowIndex) => (
        <div key={rowIndex} className="grid-row gap-3">
          {row.map((scale, colIndex) => (
            <div
              key={colIndex}
              className="grid-box "
              style={{ transform: `scale(${scale})` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
};

export default GridAnimation;
