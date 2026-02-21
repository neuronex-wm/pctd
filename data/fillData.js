
Spry.Utils.addLoadListener(function() {
var tasks;	
function loaddata(){ 
	$.getJSON('data.json', function(data) {
    
    tasks = data;
	
    initListOfTasks();   
    }); 

}




let cardContainer;

let createTaskCard = (task) => {

    let card = document.createElement('div');
    card.className = 'card shadow cursor-pointer';

    let cardBody = document.createElement('div');
    cardBody.className = 'card-body';

    let title = document.createElement('h5');
    title.innerText = task.ID;
    title.className = 'card-title';

    let color = document.createElement('div');
    color.innerText = 'PEAKLP: ' + task.peakLP;
    color.className = 'card-color';
	
	let resist = document.createElement('div');
    resist.innerText = task.Resistence;
    resist.className = 'card-resist';


    cardBody.appendChild(title);
    cardBody.appendChild(color);
	cardBody.appendChild(resist);
    card.appendChild(cardBody);
    cardContainer.appendChild(card);

}

let initListOfTasks = () => {
    if (cardContainer) {
        document.getElementById('card-container').replaceWith(cardContainer);
        return;
    }

    cardContainer = document.getElementById('card-container');
    tasks.forEach((task) => {
        createTaskCard(task);
    });
};


loaddata();
});
