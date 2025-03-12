import { useState, useEffect, useRef } from "react";

// npm install framer-motion
import { motion, AnimatePresence } from "framer-motion";

// npm install react-spinners
import { BarLoader } from "react-spinners";

// cd ui
// npm run dev


export default function App() {
  const [examples, setExamples] = useState([]);
  const [loadingExamples, setLoadingExamples] = useState(true);
  const [errorFetchingExamples, setErrorFetchingExamples] = useState(false);

  const [nextItem, setNextItem] = useState({});
  const [loadingNextItem, setLoadingNextItem] = useState(true);
  const [errorFetchingNextItem, setErrorFetchingNextItem] = useState(false);
  const hasFetchedNextItem = useRef(false);  // Prevents re-fetching in debug mode

  const [dataProgress, setDataProgress] = useState(0);

  const [leftImages, setLeftImages] = useState([]);
  const [rightImages, setRightImages] = useState([]);
  const [droppedImages, setDroppedImages] = useState(new Set());
  const [numCorrect, setNumCorrect] = useState(0);
  const [lastDroppedIndex, setLastDroppedIndex] = useState(null);
  const [isAnimatingLeft, setIsAnimatingLeft] = useState(false);
  const [isAnimatingRight, setIsAnimatingRight] = useState(false);

  const [isOpen, setIsOpen] = useState(false);
  const [evalResult, setEvalResult] = useState({});
  const [loading, setLoading] = useState(false);

  const [isButtonDisabled, setIsButtonDisabled] = useState(true);

  useEffect(() => {
    setLoadingExamples(true);
    setErrorFetchingExamples(false); // Reset error state

    fetch("http://localhost:5000/api/examples")
      .then((response) => response.json())
      .then((data) => {
        setExamples(data);
        setLoadingExamples(false);
      })
      .catch((error) => {
        console.error("Error fetching examples:", error);
        setErrorFetchingExamples(true);
        setLoadingExamples(false);
      });
  }, []);

  const fetchNextItem = () => {
    setLoadingNextItem(true); // Show "Loading..."
    setErrorFetchingNextItem(false); // Reset error state

    fetch("http://localhost:5000/api/next_item")
      .then((response) => response.json())
      .then((data) => {
        setNextItem({...data, key: data.n_seen});
        setDataProgress(Math.round(100 * nextItem.n_seen / nextItem.n_total));
        setLoadingNextItem(false);
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
        setErrorFetchingNextItem(true); // Set error state
        setLoadingNextItem(false);  // Stop loading on error
      });
  };

  const handleNextItemClick = () => {
    setIsButtonDisabled(true);
    fetchNextItem(); // Call the fetch function
  };
  
  const fetchEvaluation = async () => {
    setLoading(true); // Start loading
    try {
      const response = await fetch("http://localhost:5000/api/evaluation");
      const data = await response.json();
      setEvalResult({...data});
    } catch (error) {
      console.error("Error fetching evaluation:", error);
    }
    setLoading(false); // Stop loading
  };
  
  const handleEvaluationClick = async () => {
    await fetchEvaluation(); // Fetch data first
    setIsOpen(true); // Open the popup after image is ready
  };

  useEffect(() => {
    if (!hasFetchedNextItem.current) {
      fetchNextItem();
      hasFetchedNextItem.current = true;
    }
  }, []);

  const handleDrop = (event, side) => {
    event.preventDefault();
    const imageData = nextItem.image_base64;
    const identifier = nextItem.n_seen;
    const label = nextItem.label;
    const leftLabel = examples[0].label;
    const rightLabel = examples[1].label;
    const animationDuration = 500;  // [ms]

    if (droppedImages.has(identifier)) return;  // Prevent re-dropping

    if (side === "left") {
      setLeftImages([imageData, ...leftImages]);
      if (label == leftLabel) setNumCorrect(numCorrect + 1);
      setIsAnimatingLeft(true);
      setTimeout(() => setIsAnimatingLeft(false), animationDuration);
    } else {
      setRightImages([imageData, ...rightImages]);
      if (label == rightLabel) setNumCorrect(numCorrect + 1);
      setIsAnimatingRight(true);
      setTimeout(() => setIsAnimatingRight(false), animationDuration);
    }

    setLastDroppedIndex(0);  // Added new element at the beginning
   
    setDroppedImages(new Set([...droppedImages, identifier]))  // Mark as dropped

    setIsButtonDisabled(false);  // Enable button again
  };

  const allowDrop = (event) => {
    event.preventDefault();
  };

  const handleDragStart = (e, identifier) => {
    
    if (!droppedImages.has(identifier)) {
      e.dataTransfer.setData("text/plain", "image");
    } else {
      e.preventDefault(); // Prevent dragging if already dropped
    }
  };

  return (
    <div className="flex flex-col items-center p-4">

      <h1 className="text-2xl font-bold mb-4">Dekore Inspection Challenge</h1>
      
      <p className="mt-2 mb-4whitespace-pre-wrap">
        Can you beat the AI system in classifying the presented dekores correctly?<br />
        The system will present you with a series of images, and you have to classify them<br />
        via drag&drop into the correct list below. The example image will help you as reference.
      </p>

      {loadingExamples || errorFetchingExamples ? (
        <p>Loading...</p>
      ) : (
        <div className="flex justify-center gap-12 mt-6">
          {examples.map((example, index) => (
            <div
              key={index}
              className="flex flex-col items-center bg-gray-200 p-4 rounded-lg shadow-lg transform transition-transform duration-300 hover:scale-150"
            >
              <div className="relative overflow-hidden w-[128px] h-[128px]">
                <img
                  src={example.image_base64}
                  alt={example.label}
                  className="w-full h-full object-cover rounded"
                  onLoad={() => {
                    console.log("Examples loaded.")
                    setLoadingExamples(false);
                  }}
                  onError={() => {
                    console.log("Error loading examples.")
                    setErrorFetchingExamples(true);
                    setLoadingExamples(false);
                  }}
                />
              </div>
              <h2 className="mt-2 text-lg font-semibold">{example.label}</h2>
            </div>
          ))}
        </div>
      )}

      <div className="w-full max-w-sm mt-4 p-4 rounded-full">
        <div
          className="bg-blue-500 text-xs text-center text-white p-1 rounded-full"
          style={{ width: `${dataProgress}%` }}
        >
          {dataProgress}%
        </div>
      </div>

      <div className="flex gap-4">  
        <button
          onClick={handleNextItemClick}
          disabled={isButtonDisabled}
          className={`px-4 py-2 rounded ${
            isButtonDisabled ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"
          } text-white shadow-lg`}
        >
          {isButtonDisabled ? "Drag & Drop" : "Next Image"}
        </button>

        <button
          onClick={handleEvaluationClick}
          className="px-4 py-2 bg-blue-500 text-white rounded shadow-lg hover:bg-blue-600"
        >
          Evaluate Decisions
        </button>
      </div>

      {loading && (  // Loading spinner
        <div className="flex justify-center items-center mt-4">
          <BarLoader color="#3b82f6" size={15} />
          <p className="ml-4">Loading Evaluation...</p>
        </div>
      )}
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-white p-6 rounded-lg shadow-lg max-w-sm text-center"
              initial={{ rotateZ: -360, opacity: 0 }}
              animate={{ rotateZ: 0, opacity: 1 }}
              exit={{ rotateZ: -360, opacity: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-xl font-semibold mb-2">Evaluation Results</h2>
              <div className="flex justify-center items-center">
                  <img
                    src={evalResult.image_base64}
                    alt="Confusion Matrix"
                    className="rounded-lg mb-4"
                  />
              </div>
              <p className="mb-4">Accuracy of the AI system is: {evalResult.acc}</p>
              <p className="mb-4">Accuracy of the human player is: {(100 * numCorrect / droppedImages.size).toFixed(2)}</p>
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 bg-red-500 text-white rounded shadow-lg hover:bg-red-600"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <div className="flex justify-center">  
        {loadingNextItem || errorFetchingNextItem ? (
          <p>Loading...</p>
        ) : (
          nextItem.image_base64 && (
            <img
              key={nextItem.key}
              src={nextItem.image_base64}
              alt="Draggable"
              className={`rounded mt-4 cursor-grab bg-white p-4 transition-all duration-300 ${
                isButtonDisabled ? "opacity-100" : "opacity-50 grayscale"
              }`}
              draggable="true"
              onDragStart={(e) => handleDragStart(e, nextItem.n_seen)}
              onLoad={() => {
                console.log("Next item loaded:", nextItem.n_seen);
                setLoadingNextItem(false);
              }}
              onError={() => {
                console.error("Failed to load next item:", nextItem.n_seen);
                setErrorFetchingNextItem(true);
                setLoadingNextItem(false);
              }}
            />
          )
        )}
      </div>

      <div className="flex w-full max-w-4xl gap-4 justify-center py-4">
        <div
          className="flex flex-col items-center w-[200px] min-h-[200px] bg-gray-200 p-4 rounded-lg"
          onDrop={(e) => handleDrop(e, "left")}
          onDragOver={allowDrop}
        >
          <h2 className="text-lg font-semibold mb-2">
            {examples.length > 0 ? `${examples[0].label} Images` : "Loading..."}
          </h2>
          {leftImages.map((img, index) => (
            <div key={index} className="relative flex justify-center items-center mb-2">
              <img
                src={img}
                alt="Dropped"
                className="w-[128px] h-[128px] rounded shadow-lg"
              />
              {isAnimatingLeft && lastDroppedIndex === index && (
                <span className="absolute inset-0 w-[128px] h-[128px] rounded-full bg-blue-400 opacity-75 animate-ping"></span>
              )}
            </div>
          ))}
        </div>
        <div
          className="flex flex-col items-center w-[200px] min-h-[200px] bg-gray-200 p-4 rounded-lg"
          onDrop={(e) => handleDrop(e, "right")}
          onDragOver={allowDrop}
        >
          <h2 className="text-lg font-semibold mb-2">
            {examples.length > 0 ? `${examples[1].label} Images` : "Loading..."}
          </h2>
          {rightImages.map((img, index) => (
            <div key={index} className="relative flex justify-center items-center mb-2">
              <img
                src={img}
                alt="Dropped"
                className="w-[128px] h-[128px] rounded shadow-lg"
              />
              {isAnimatingRight && lastDroppedIndex === index && (
                <span className="absolute inset-0 w-[128px] h-[128px] rounded-full bg-blue-400 opacity-75 animate-ping"></span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
