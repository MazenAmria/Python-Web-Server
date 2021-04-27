window.addEventListener('load', function () {
  const cardTemplate = `
    <div class="col-6">
      <div class="card shadow" style="height: 100%">
        <div class="card-body" style="height: 40%">
          <h5 class="card-title">
            <nav class="navbar text-dark">
              <span class="navbar-brand">{{ key }}</span>
            </nav>
          </h5>
          <p class="card-text">{{ value }}</p>
        </div>
      </div>
    </div>
`;
});
