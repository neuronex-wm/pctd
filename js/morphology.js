import ImageViewer from "iv-viewer";
import "/js/iv-viewer/dist/iv-viewer.css";

const images = [
  {
    small: "../images/morph Cells/cell1.png",
    big: "../images/morph Cells/cell1.png"
  },
  {
    small: "../images/morph Cells/cell2.png",
    big: "../images/morph Cells/cell2.png"
  }
];

let curImageIdx = 1;

const total = images.length;
const wrapper = document.querySelector("#image-gallery");

const curSpan = wrapper.querySelector(".current");
const viewer = new ImageViewer(wrapper.querySelector(".image-container"));
window.viewer = viewer;
// display total count
wrapper.querySelector(".total").innerHTML = total;

function showImage() {
  const imgObj = images[curImageIdx - 1];
  viewer.load(imgObj.small, imgObj.big);
  curSpan.innerHTML = curImageIdx;
}

wrapper.querySelector(".next").addEventListener("click", function(evt) {
  curImageIdx++;
  if (curImageIdx > total) curImageIdx = 1;
  showImage();
});

wrapper.querySelector(".prev").addEventListener("click", function(evt) {
  curImageIdx--;
  if (curImageIdx < 0) curImageIdx = total;
  showImage();
});

// initially show image
showImage();
