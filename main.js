function redirect(url) {
  window.location.href = url;
}
window.addEventListener('load', function () {
  const cardTemplate = `
    <div class="col">
      <div
        class="card shadow"
        style="height: 100%; cursor: pointer;"
        onclick="redirect('{{ url }}')"
      >
        <img
          src="{{ img }}"
          class="card-img-top"
          style="height: 60%; object-fit: cover"
        />
        <div class="card-body" style="height: 40%;">
          <h5 class="card-title">
            <nav class="navbar text-dark">
              <span class="navbar-brand">{{ title }}</span>
            </nav>
          </h5>
          <p class="card-text">{{ text }}</p>
        </div>
      </div>
    </div>
`;

  fetch('/projects.json')
    .then((response) => response.json())
    .then((projects) => {
      renderedProjects = '';

      for (project of projects) {
        rendered = cardTemplate;

        for (key in project) {
          rendered = rendered.replace('{{ ' + key + ' }}', project[key]);
        }

        renderedProjects = renderedProjects.concat(rendered);
      }

      document.getElementById('projects').innerHTML = renderedProjects;
    });
});
