'use client'
import React, { useState, useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import MapStyleSelector from './StyleSelector';
import axios from 'axios';

const Map = () => {
  // const [counts, setCounts]
  const [resultImage, setResultImage] = useState(null); const [map, setMap] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(2); // Initial zoom level
  const [imageData, setImageData] = useState(null);
  const [threshold, setThreshold] = useState(50);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStyle, setSelectedStyle] = useState('satellite-v9');
  const [screenshot, setScreenshot] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const intervalRef = useRef(null);
  const mapContainerRef = useRef(null); // Ref for map container
  const [confidence, setConfidence] = useState(0.1);
  const [pngimage, setPng] = useState(null);
  const [preds, setPreds] = useState(null);
  const [showPreviewCanvas, setShowPreviewCanvas] = useState(false);
  const canvasRef = useRef(null);
  const [previewCanvas , setPreviewCanvas ] = useState(null);
  const [modifiedImagex, setModifiedImagex] = useState(null)
  const clickCounter = useRef(0);
  const [stop ,setStop] = useState(false);
  const [path, setPath] = useState(false);

  const mapStyles = [
    { label: 'Satellite', value: 'satellite-v9', image: '/sat.png' },
    { label: 'Streets', value: 'streets-v12', image: '/street.png' },
    { label: 'Dark', value: 'dark-v11', image: '/dark.png' },
    { label: 'Light', value: 'light-v11', image: '/light.png' },
    { label: 'Satellite Streets', value: 'satellite-streets-v12', image: '/sat2.png' },
    { label: 'Navigation Day', value: 'navigation-day-v1', image: '/day.png' },
    { label: 'Navigation Night', value: 'navigation-night-v1', image: '/night.png' }
  ];


  useEffect(() => {
    mapboxgl.accessToken = 'pk.eyJ1Ijoic2FoaWx4IiwiYSI6ImNsdW56eWg1czFqaTkybW4ycGZka2ZkYTUifQ.GTewW_1jNHqC4C_0cb0zNg';
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: `mapbox://styles/mapbox/${selectedStyle}`,
      center: [80, 20],
      zoom: zoomLevel,

      projection: 'globe',
    });
    console.log(map.zoom)
    map.on('style.load', () => {
      map.setFog({
        color: 'rgb(186, 210, 235)',
        'high-color': 'rgb(36, 92, 223)',
        'horizon-blend': 0.02,
        'space-color': 'rgb(11, 11, 25)',
        'star-intensity': 0.6
      });
    });

    setMap(map);

    const rotateMap = () => {
      const bearing = map.getBearing() + 2;
      map.easeTo({ bearing: bearing });
    };

    intervalRef.current = setInterval(rotateMap, 50);

    const stopRotationOnClick = () => {
      clearInterval(intervalRef.current);
      map.off('click', stopRotationOnClick);
    };

    map.on('zoom', () => {
      setZoomLevel(map.getZoom());
    });


    map.on('click', stopRotationOnClick);

    return () => {

      // Cleanup: remove event listener on unmount
      map.off('zoom', () => {
        setZoomLevel(mapInstance.getZoom());
      });

      clearInterval(intervalRef.current);
      map.off('click', stopRotationOnClick);
    };
  }, [selectedStyle]);



  const handleChange = (e) => {
    const { value } = e.target;
    setSearchQuery(value);
    handleSearch(value);
  };

  const handleSearch = async (query) => {
    if (map && query) {
      console.log('true')
      try {
        const response = await fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=pk.eyJ1Ijoic2FoaWx4IiwiYSI6ImNsdW56eWg1czFqaTkybW4ycGZka2ZkYTUifQ.GTewW_1jNHqC4C_0cb0zNg`);
        console.log('searched')

        const data = await response.json();
        console.log('data', data)

        if (data.features.length > 0) {
          setSearchResults(data.features);
        } else {
          setSearchResults([]);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    } else {
      setSearchResults([]);
    }
  };

  const handleResultClick = (result) => {
    const [longitude, latitude] = result.center;
    map.flyTo({ center: [longitude, latitude], zoom: 16 });
    clearInterval(intervalRef.current);

    setSearchQuery('');
    setSearchResults([]);
  };

  const handleStyleChange = (style) => {
    setSelectedStyle(style);
    if (map) {
      map.setStyle(`mapbox://styles/mapbox/${style}`);
    }
  };

  const captureMapScreenshot = async () => {
    try {
      const { latitude, longitude, zoom, width, height } = getMapParameters();
      const response = await fetch(`https://api.mapbox.com/styles/v1/mapbox/${selectedStyle}/static/${longitude},${latitude},${zoom}/${width}x${height}?format=png&access_token=pk.eyJ1Ijoic2FoaWx4IiwiYSI6ImNsdW56eWg1czFqaTkybW4ycGZka2ZkYTUifQ.GTewW_1jNHqC4C_0cb0zNg`);
      if (!response.ok) {
        throw new Error('Failed to fetch static map image');
      }
      const imageBlob = await response.blob();
      
      // Convert image to PNG
      const fileReader = new FileReader();
      fileReader.onload = () => {
        const imageUrl = fileReader.result;

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.onload = () => {
          const scaledWidth = 1000;
          const scaledHeight = 600;
          canvas.width = scaledWidth;
          canvas.height = scaledHeight;
          ctx.drawImage(img, 0, 0,scaledWidth, scaledHeight);
          const pimage = canvas.toDataURL('image/png');
          // Save both original image and PNG in state variables
          setScreenshot(imageUrl);
          setPng(pimage);
          setShowPreview(true);
        };
        img.src = imageUrl;
      };
      fileReader.readAsDataURL(imageBlob);

    } catch (error) {
      console.error('Error capturing screenshot:', error);
    }
  }
  //     const imageUrl = URL.createObjectURL(imageBlob);
  //     const file = new File([imageBlob], "screenshot.jpg", { type: "image/jpeg" });
  //     console.log('img',imageUrl)
  //     console.log('fileeeeeeeeeeeeeeeee',file)
  //     setScreenshot(imageUrl);
  //     setShowPreview(true);
  //   } catch (error) {
  //     console.error('Error capturing screenshot:', error);
  //   }
  // };


  const sendImageForPrediction = async () => {
    try {
      // Convert the screenshot object to base64
      const image = screenshot

      await axios({
        method: "POST",
        url: "https://classify.roboflow.com/tree-segmentation-8bjvl/5",
        params: {
          api_key: "iai1ejzQyiSEer0AALCB"
        },
        data: image,
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        }
      })
        .then(function (response) {
          setImageData(response.data);
          console.log(response.data);
        })
        .catch(function (error) {
          console.log(error.message);
        });
    } catch (error) {
      console.error(error);
    }
  };

  const handlePrediction = () => {
    setResultImage(null);

    sendImageForPrediction();
  }

  const handlePredict = async () => {
    try {
      setModifiedImagex(null);
      setImageData(null);
      const byteString = atob(pngimage.split(",")[1]);
      const arrayBuffer = new ArrayBuffer(byteString.length);
      const uint8Array = new Uint8Array(arrayBuffer);
      for (let i = 0; i < byteString.length; i++) {
        uint8Array[i] = byteString.charCodeAt(i);
      }
      const blob = new Blob([uint8Array], { type: 'image/jpeg' });
      const file = new File([blob], "image.jpg", { type: 'image/jpeg' })
      const formData = new FormData();
      formData.append("image", file);
      formData.append("confidence", confidence);
      const response = await axios.post("http://localhost:5000/predict", formData, {
        responseType: 'blob',
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log('respose', response)
      setResultImage(URL.createObjectURL(response.data));
      const response2 = await axios.post("http://localhost:5000/predict/list", formData, {

        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      console.log('respose2', response2)
      const listData = response2.data;

      // Map numbers to names
      const numberToNameMap = {
        0.0: 'Building',
        1.0: 'Green',
        2.0: 'Land',
        3.0: 'Tree',
        4.0: 'Water'
      };

      // Count occurrences of each number
      const counts = {};
      listData.forEach(number => {
        const name = numberToNameMap[number];
        counts[name] = counts[name] ? counts[name] + 1 : 1;


      });
      console.log('lsit datat', counts)

      // Log counts
      setPreds(counts)
      console.log('pressssssssss', preds)
    } catch (error) {
      console.error("Error:", error);
    }
  };



  const handleConfidenceChange = async (e) => {
    setConfidence(e.target.value);
    await handlePredict();

  };
  const handleClick = (event) => {
    console.log("Click event occurred on the canvas");
    // Get click coordinates relative to the canvas
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    console.log("Clicked coordinates (x, y):", x, y);

    // Draw circle at clicked coordinates
    ctx.fillStyle = 'red';
    ctx.beginPath();
    ctx.arc(x, y, 10, 0, Math.PI * 2);
    ctx.fill();

    console.log("Circle drawn at clicked coordinates");

    // Save the modified canvas as an image
    const modifiedImage = canvas.toDataURL('image/png');
    console.log("Modified image data URL:", modifiedImage);
    setModifiedImageURL(modifiedImage);
};



const handleBrushing = () => {
  console.log("Function started");

  if (!canvasRef.current) {
      const canvas = document.createElement('canvas');
      canvasRef.current = canvas;

      console.log("Canvas element created:", canvas);

      const ctx = canvas.getContext('2d');
      console.log("Canvas context:", ctx);

      // Style the canvas to ensure visibility and interactivity
      canvas.style.position = 'absolute';
      canvas.style.top = '7.7%';
      canvas.style.left = '5.4%';
      canvas.style.zIndex = '30';
      
      canvas.style.border = '1px solid black';
      canvas.style.cursor = 'pointer';  // Change cursor to pointer

      // Append the canvas to the body (or any other container)
      document.body.appendChild(canvas);
      console.log("Canvas appended to DOM");

      // Add hover effect to change cursor style
      canvas.addEventListener('mouseover', () => {
          canvas.style.cursor = 'pointer';
      });

      canvas.addEventListener('mouseout', () => {
          canvas.style.cursor = 'default';
      });

      const image = new Image();

      // Load the image onto the canvas
      image.onload = () => {
          console.log("Image loaded");
          canvas.width = image.width;
          canvas.height = image.height;
          ctx.drawImage(image, 0, 0);
          console.log(canvas.width, canvas.height);

          // Add click event listener to the canvas
          const handleClick = (event) => {
              console.log('Click event listener triggered');

              // Get click coordinates relative to the canvas
              const rect = canvas.getBoundingClientRect();
              const x = event.clientX - rect.left;
              const y = event.clientY - rect.top;

              // Draw circle at clicked coordinates
              ctx.fillStyle = 'red';
              ctx.beginPath();
              ctx.arc(x, y, 10, 0, Math.PI * 2);
              ctx.fill();
              console.log(`Circle drawn at (${x}, ${y})`);

              // Increment click counter
              clickCounter.current += 1;

              // Save the modified canvas as an image
              const modifiedImage = canvas.toDataURL('image/png');
              setModifiedImagex(modifiedImage);
              console.log('Modified image URL set');

              // Remove the event listener after 2 clicks
              if (clickCounter.current >= 2) {
                  canvas.style.display = 'none';
                  setStop(!stop)
                  canvas.removeEventListener('click', handleClick);
                  console.log('Click event listener removed');
              }
          };

          canvas.addEventListener('click', handleClick);
          console.log('Click event listener added');
      };

      // Set the source of the image
      image.src = pngimage;
      console.log('Source set');
  } else {
      console.log('Canvas already exists, skipping creation');
  }
};
   



      
    
  




  const getMapParameters = () => {
    const center = map.getCenter();
    console.log('Center:', center);
    const zoom = map.getZoom();
    console.log('Zoom:', zoom);
    const width = Math.min(mapContainerRef.current.offsetWidth, 1280);
    console.log('Width:', width);
    const height = mapContainerRef.current.offsetHeight;
    console.log('Height:', height);
    const latitude = center.lat;
    console.log('Latitude:', latitude);
    const longitude = center.lng;
    console.log('Longitude:', longitude);
    return { latitude, longitude, zoom, width, height };
  };

  const handleClosePreview = () => {
    setStop(!stop);
    canvasRef.current = null;
    setShowPreview(false);
    setResultImage(null);
    setImageData(null);
    setScreenshot(null); // Reset screenshot
    setPreds(null);
    setModifiedImagex(null);
  };
  const renderPredictions = () => {
    const displayedImageWidth = '40%'; // Adjust as needed
    const originalImageWidth = 1280; // Original image width
    const widthRatio = originalImageWidth / displayedImageWidth;
  }
  const handleChangeThreshold = (e) => {
    setThreshold(parseFloat(e.target.value));
  };
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !showPreview) { // Set cropping state to true
      }
    };

    document.addEventListener('keydown', handleKeyPress);

    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [showPreview]);




  return (
    <div className='h-screen w-screen
    max-sm:h-screen max-sm:w-screen
    '>
      <div className="relative w-full h-screen
      max-sm:h-screen max-sm:w-full
      ">
        <div ref={mapContainerRef} id="map" className="absolute top-0 left-0 w-full h-full
        max-sm:absolute max-sm:top-0 max-sm:left-0 max-sm:w-full max-sm:h-full
        "></div>
        <div className="2xl:absolute 2xl:top-4 2xl:left-4
        max-sm:absolute max-sm:top-4 max-sm:left-4
        ">
          <input
            type="text"
            value={searchQuery}
            onChange={handleChange}
            placeholder="Search location..."
            className="2xl:p-2 2xl:h-6 2xl:rounded 2xl:opacity-70 text-black
            max-sm:p-2 max-sm:h-10 max-sm:opacity-70 max-sm:rounded-md
            "
          />
          <button onClick={captureMapScreenshot} className="mt-2
          max-sm:mt-2 max-sm:text-sm
          ">Take Screenshot</button> {/* Button to capture screenshot */}

          <div className="mt-2 opacity-80 text-black
          max-sm:text-sm">
            {searchResults.map((result, index) => (
              <div key={index} onClick={() => handleResultClick(result)} className="cursor-pointer hover:bg-gray-200 px-3 py-2 border-b bg-white border-gray-300">{result.place_name}</div>
            ))}
          </div>
        </div>
        <div className="absolute bottom-0 left-0 2xl:text-2xl bg-white p-2 rounded shadow-md text-black z-20
        max-sm:text-sm max-sm:h-9
        ">
          Zoom Level: {zoomLevel.toFixed(2)}
        </div>
        <div className='absolute right-0 top-0
        max-sm:h-10 max-sm:w-20
        ' >
          <MapStyleSelector mapStyles={mapStyles} selectedStyle={selectedStyle} handleStyleChange={handleStyleChange} />
        </div>
        {/* <div className="absolute top-4 right-4 text-black">
  <select value={selectedStyle} onChange={(e) => handleStyleChange(e.target.value)}>
    {mapStyles.map((style, index) => (
      <option key={index} value={style.value}>
        {style.label}
      </option>
    ))}
  </select>
</div> */}
      </div>
      {showPreview && screenshot && (
        <div className="absolute justify-center top-[0%] left-[0%] snap-center w-full h-full flex  bg-gray-900 bg-opacity-75 z-20
        max-sm:h-[screen] max-sm:w-[screen] 
        ">
          <div className="absolute h-[full-100px] w-[1400px] m-10 backdrop-blur-[3px] bg-opacity-10 bg-blue-300 border border-slate-400 p-4 rounded-xl shadow-lg
         max-sm:h-[700px] max-sm:w-[380px] max-sm:flex-col  max-sm:justify-center max-sm:backdrop-blur-sm max-sm:bg-transparent max-sm:outline 
         ">
            <button className="absolute -top-6 -right-6 backdrop-blur-sm border-slate-100 border p-2 rounded-md z-50 text-gray-200  hover:text-gray-400
  max-sm:-top-8 max-sm:right-1
  " onClick={handleClosePreview}>Close</button> {/* Close button */}
            <div className='flex h-full w-full
  max-sm:h-[400px] max-sm:w-[400px] max-sm:flex-col
  '>
              <div className='flex-col h-[600px] w-[1000px] 
  max-sm:flex-col max-sm:h-[700px] max-sm:w-[350px]
  '>
                <div className=' rounded-xl' >
                  <img

                    src={screenshot}
                    alt="Screenshot"
                    className={`h-[600px] w-[1000px] rounded-xl border border-slate-300 ${resultImage !== null ? 'hidden' : 'block'} ${previewCanvas !== null ? 'hidden' : 'block'}
    max-sm:h-[400px] max-sm:w-[350px]
    `}
                  />
                 <div className={`absolute ${canvasRef !== null ?'block':'hidden'} left-4 top-4 h-[600px] w-[1000px] z-30 opacity-100`}>
          <canvas className={` absolute ${canvasRef !== null ?'block':'hidden'} rounded-[5px] border border-opacity-10 border-white  left-0 top-0 h-[600px] w-[1000px] z-40 opacity-100`} ref={canvasRef.current}/>
         </div>
      
      {modifiedImagex && 
            <img className={` absolute left-4 top-4 z-50 h-[600px] w-[1000px] outline-dotted scale-100 ${stop ? 'block':'hidden'}`} src={modifiedImagex} alt='x' />
          }
                  {resultImage && <img className=' absolute left-5 h-[600px] w-[1000px] rounded-xl border-2 border-slate-300  
max-sm:h-[400px] max-sm:w-[350px] max-sm:outline 
' src={resultImage} alt="Result" />}

                  <div className={`absolute -bottom-10 rounded-md h-10 w-[350px] justify-center items-center backdrop:blur-sm border border-blue-200
            max-sm:-bottom-14 ${resultImage !== null ? 'block' : 'hidden'}
            `}>
                    {resultImage && <div className=' flex m-2 '>
                      <input
                        className=' backdrop-blur-md
             max-sm:
             '
                        type="range"
                        min="0.01"
                        max="1"
                        step="0.01"
                        value={confidence}
                        onChange={handleConfidenceChange}
                      />

                      <span className='ml-2'>   {confidence}    Confidence Level</span> </div>}
                  </div>

                  <div className='absolute -top-6 left-4 '>
                    {imageData && (

                      <div className='absolute -bottom-10 rounded-md  w-[350px]  bg-black outline outline-yellow-300 '>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.01"
                          value={threshold}
                          onChange={handleChangeThreshold}
                          className="h-6 w-40"
                        />
                        {/* <img src={screenshot} alt="Your Image" style={{ maxWidth:'100%' }} /> */}
                        <div className='outline outline-slate-950 absolute  h-[600px] w-[1000px] object-contain '>
                          {imageData.predictions.map((prediction, index) => {
                            if (prediction.confidence >= threshold) {
                              return (
                                <div
                                  className="absolute "
                                  key={index}
                                  style={{
                                    top: prediction.y / 1.85, // Adjusted position
                                    left: prediction.x / 2.1, // Adjusted position
                                    width: prediction.width / 1.8, // Adjusted width
                                    height: prediction.height / 1.8, // Adjusted height
                                    border: '4px solid green',
                                    boxSizing: 'border-box',
                                  }}
                                >{prediction.class}</div>
                              );
                            } else {
                              return null;
                            }
                          })}
                        </div>
                      </div>

                    )}
                  </div>
                </div>

              </div>
              <div className='flex-col w-[200px] justify-center items-center m-8
  max-sm:flex
  '>
                <button className=" h-10 w-20 justify-center text-gray-500  hover:text-gray-800 rounded-lg m-2  bg-slate-200" onClick={handlePrediction}>Predict</button>
                <div>
                  {/* Assuming you have a way to set the image state */}

                  <button className=" h-10 w-40 justify-center text-gray-500  hover:text-gray-800 rounded-lg m-2 bg-slate-200" onClick={handlePredict}>Run Inference </button>
                  <button className="h-10 w-40 justify-center text-gray-500 hover:text-gray-800 rounded-lg m-2 bg-slate-200" onClick={()=>setPath(!path)}>Path Generation</button>
                  <button className={`h-10 w-40 justify-center text-gray-500 hover:text-gray-800 rounded-lg m-2 bg-slate-200 ${path?'block':'hidden'}`} onClick={handleBrushing}>Mark Two Points</button>
                  <button className={`h-10 w-40 justify-center text-gray-500 hover:text-gray-800 rounded-lg m-2 bg-slate-200 ${stop === true && path === true ? 'show' : 'hidden'}`}> Generate Path</button>


                  {preds && preds.hasOwnProperty('Tree') ? (
                    <li className='h-10 w-50 text-black' key="Tree">
                      Tree: {preds['Tree']}
                    </li>
                  ) : (
                    <li className={`h-10 w-50 text-black ${preds === null?'hidden':'block'} `} key="Tree">
                      No Tree Detected
                    </li>
                  )}

                </div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

export default Map;
